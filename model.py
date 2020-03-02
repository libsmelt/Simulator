#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import sys
import logging
import config
import helpers
import re

sys.path.append(config.MACHINE_DATABASE_SCRIPTS)
import topology_parser

import itertools
import gzip

from multimessage import MultiMessage

# --------------------------------------------------
class Model(object):

    def __init__(self, graph=None):
        """
        We initialize models with the graph
        """

        print ('Initializing Model(%s)' % self.get_name())

        self.send_cost = {}
        self.recv_cost = {}

        self.send_history = {}
        self.mm = None # MultiMessage benchmark - see NetosMachine
        self.enable_mm = False

        assert graph == None

        # Topology parser
        # --------------------------------------------------
        try:
            self.machine_topology = topology_parser.parse_machine_db(self.get_name(), 'machinedb/')
            print ('Parsing machine topology was successful, machine is %s' % \
                            (topology_parser.generate_short_name(self.machine_topology)))
        except:
            helpers.warn('Warning: topology parser did not find machine data')
            raise
            exit (0)


        # Pairwise
        # --------------------------------------------------

        # Parse pairwise send and receive costs. We need this to
        # build the graph with the pairwise measurements.
        self._parse_receive_result_file()
        self._parse_send_result_file()


        # Multimessage
        # --------------------------------------------------
        mm_fname = '%s/%s/multimessage.gz' % \
                   (config.MACHINE_DATABASE_DATA, self.get_name())

        self.mm = None

        print ('Reading multimessage data: ', mm_fname)
        try:
            f = gzip.open(mm_fname, 'r')
            self.mm = MultiMessage(f, self)
            f.close()
        except IOError:
            print ('No multimessage data for this machine')
        except Exception as e:
            helpers.warn('Unable to read multimessage data' + str(e))

        # Build graph and reset
        # --------------------------------------------------
        self.graph = self._build_graph()
        self.reset()


    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return None

    def get_num_numa_nodes(self):
        """Get the number of NUMA nodes
        """
        return len(self.machine_topology['NUMA'].get())


    def get_num_cores(self, only_mc=False):
        """Get number of cores.

        param only_mc: only return the cores that are active in the
        multicast.

        """
        if only_mc:
            return len(self.get_cores(True))
        else:
            return self.machine_topology['numcpus']


    def get_cores_per_node(self):
        """Assumptions: All NUMA nodes have the same number of cores.

        """
        return len(self.machine_topology['NUMA'].get()[0])


    def get_send_history_cost(self, sender, cores, corrected=False):
        """Return the send cost for the given history of cores.

        @param sender int The core ID of the sender.
        @param cores list(int) The cores in the send history.

        @param corrected If set to True, enables correction of the
            n-send costs based on multimessage data.

        """
        cost = 0

        for c in cores:
            cost += self.get_send_cost(sender, c, False, False)

        # Correct if requested
        if self.enable_mm and corrected and self.mm:
            cost /= self.mm.get_factor(sender, cores)

        return cost


    def get_send_cost(self, sender, receiver, corrected=False, add_history=False):
        """Determine the send cost for a single message on the link <sender>
        to <receiver> given the sender's previous history.

        @param corrected If corrected is True, correct the send cost
        based on the previous history

        """
        if (sender==receiver):
            return 0

        cost = -1

        if corrected:
            cost = self.get_send_cost_for_history(sender, receiver,
                                                  self.send_history.get(sender, []))

        else:
            if not (sender, receiver) in self.send_cost:
                cost = sys.maxsize
            else:
                cost = self.send_cost[(sender, receiver)]

        if add_history:
            self.add_send_history(sender, receiver)

        assert cost>0
        return cost


    def get_send_cost_for_history(self, sender, receiver, cores):

        """Determine the cost of sending one individual message from <sender>
        to <receiver> given the previous send history <cores>

        Read from pairwise n-receive and scale by the factor given in
        multimessage.

        """

        cost = self.get_send_cost(sender, receiver, False, False)

        assert not receiver in cores # otherwise, we would repeatedly
                                     # send to the same core (chances
                                     # are the receiving core has been
                                     # added to the send history
                                     # before actually sending to it)

        if self.enable_mm:
            cost /= self.mm.get_factor(sender, cores + [receiver])

        return cost


    def get_numa_information(self):
        """
        Return information on NUMA nodes. This is a a list of
        list. Every element of the outer list represents a NUMA node
        and the inner list the cores in that NUMA node.
        """
        return self.machine_topology['NUMA'].get()


    # --------------------------------------------------
    # Helpers
    def get_cores(self, only_mc=False):
        """Return a list of cores

        @param only_mc If set to true, only return nodes that
        participate in multicast.

        """
        c = list(itertools.chain.from_iterable(self.machine_topology['NUMA'].get()))
        c = self.filter_active_cores(c, only_mc)
        return c


    def filter_active_cores(self, n, only_active):

        if config.args.multicast and only_active:
            n = [ n_ for n_ in n if n_ in map(int, config.get_mc_group()) ]

        return n


    def output_graph(self):
        """ Write the graph out to disk as <machine_name>_graph
        """
        helpers.output_graph(self.graph, '%s_graph' % self.get_name())

    # --------------------------------------------------
    # Methods used for building overlay + scheduling
    def get_graph(self):
        return self.graph

    def on_same_numa_node(self, core1, core2):
        """
        Return whether two nodes are in the same NUMA region
        """
        for node in self.get_numa_information():
            if core1 in node:
                return core2 in node
        return None


    def get_numa_node_by_id(self, nidx):
        """Get all cores on the given NUMA node
        """
        return self.machine_topology['NUMA'].get()[nidx]


    def get_numa_node(self, core1):
        """Return all cores that are on the same NUMA node then the given core.

        This works as long as get_numa_information is implemented
        correctly for a given machine.
        """
        numa_node = []
        for node in self.graph.nodes():
            if self.on_same_numa_node(core1, node):
                numa_node.append(node)
        return numa_node


    def get_numa_id(self, c):
        """Determine ID of the NUMA node <core1> resides on.
        """
        nodes = self.machine_topology['NUMA'].get()
        for (n, i) in zip(nodes, range(len(nodes))):
            if c in n:
                return i


    def get_root_node(self):
        return None

    def _parse_receive_result_file(self):
        """
        Parse pairwise receive cost results measure with the UMP receive
        benchmark in the Barrelfish tree.

        We then use these measurements for the receive cost in the simulator

        """
        fname = '%s/%s/pairwise-nsend_receive' % \
                (config.MACHINE_DATABASE_DATA, self.get_name())
        print ('Reading receive costs from %s' % fname)
        f = open(fname)
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('(\d+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)', l)
            if m:
                (src, dest, cost) = (int(m.group(1)),
                                     int(m.group(2)),
                                     float(m.group(3)))
                assert (src, dest) not in self.recv_cost
                self.recv_cost[(src, dest)] = cost
        assert len(self.recv_cost.items())>0

    def _parse_send_result_file(self):
        """Parse pairwise send cost results.

        For each pair of cores, the input values indicate the cost of
        sending a message between that pair of cores.

        """
        fname = '%s/%s/pairwise-nsend_send' % \
                (config.MACHINE_DATABASE_DATA, self.get_name())
        print ('Reading send costs from %s' % fname)
        f = open(fname)
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('(\d+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)', l)
            if m:
                (src, dest, cost) = (int(m.group(1)),
                                     int(m.group(2)),
                                     float(m.group(3)))
                assert (src, dest) not in self.send_cost
                self.send_cost[(src, dest)] = cost
        assert len(self.send_cost.items())>0


    def get_receive_cost(self, src, dest):
        """
        Return the receive cost for a pair (src, dest) of cores

        This is the cost on dest to receive a message from src.

        """
        if (src==dest):
            return 0
        if not (src, dest) in self.recv_cost:
            return sys.maxsize

        return self.recv_cost[(src, dest)]


    def get_receive_send_ratio(self):
        """Get ratio of receive and send costs

        """

        import tools

        cmax = self.get_num_cores()

        sends = []
        recvs = []

        for s in range(cmax):
            for r in range(cmax):
                sends.append(self.query_send_cost(s, r))
                recvs.append(self.get_receive_cost(s, r))

        (s_avg, _, _, s_min, s_max) = tools.statistics(sends)
        (r_avg, _, _, r_min, r_max) = tools.statistics(recvs)


        return s_avg/r_avg, s_max/r_max, s_min/r_min


    def update_edge(self, src, dest, topology):
        """Modifies the topolgy by adding a new edge.

        Adds edge src -> dest and removing any old eges n ->
        dest. Also updates the send history.

        @param topolgy The topology to update

        """
        num = 0
        prev_parent = None

        for c in self.get_cores():

            # Delete existing edge
            if topology.has_edge((c, dest)):

                prev_parent = c
                topology.del_edge((c, dest))
                num += 1

        assert num == 1 # Make sure we only deleted one edge

        # Add new one
        topology.add_edge((src, dest), \
            self.graph.edge_weight((src, dest)))

        # Update the send history
        assert dest in self.send_history[prev_parent]
        self.send_history[prev_parent].remove(dest)

        self.add_send_history(src, dest)


    def reset(self):
        ## XXX Also need to reset send history on an individual node
        ## for barriers etc, when reverting from reduction to ab
        if self.send_history:
            logging.info(('Resetting send history' + str(self.send_history)))
        self.send_history = {}


    def add_send_history(self, src, dest):
        """Add the given <src> to <dest> communication to the send
        history. This is triggered when a message as actually going to
        be sent.

        @param src  Source core
        @param dest Destination core

        """
        self.send_history[src] = self.send_history.get(src, []) + [dest]
