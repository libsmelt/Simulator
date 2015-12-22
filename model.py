# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import pdb
import logging
import topology_parser
import config
import helpers
import re

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Model(object):

    evaluation = None
    send_cost = {}
    recv_cost = {}

    def __init__(self, graph):
        """
        We initialize models with the graph
        """
        assert (len(graph.nodes())>0)
        self.graph = graph
        try:
            print 'Looking for measurements/coresenum_print_%s' % \
                self.get_name()
            self.machine_topology = topology_parser.parse_machine_db(self.get_name())
        except:
            print 'Warning, did not find coresenum data for machine'
            self.machine_topology = None
            pass


    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return None

    def get_num_numa_nodes(self):
        return None

    def get_num_cores(self):
        return None

    def get_cores_per_node(self):
        print helpers.bcolors.WARNING + "Warning: Deprecated?" + helpers.bcolors.ENDC
        assert self.get_num_numa_nodes() is not None # Should be overriden in childs
        if self.get_num_numa_nodes()>0:
            return self.get_num_cores() / self.get_num_numa_nodes()
        else:
            return self.get_num_cores()

    # Transport cost
    def get_cost_within_numa(self):
        print helpers.bcolors.WARNING + "Warning: Deprecated?" + helpers.bcolors.ENDC
        return 1

    def get_cost_across_numa(self):
        print helpers.bcolors.WARNING + "Warning: Deprecated?" + helpers.bcolors.ENDC
        return 10

    # Node processing cost
    def get_receive_cost(self, src, dest):
        """
        The cost of receive operations on dest for messages from
        src. This is essentially the time required for the memory read
        in case of a new message, which in turn is the time required
        by the cache-coherency protocol to update the (at this point
        invalid) cache-line in the local cache with the updates
        version in the senders cache.
        """
        return self._get_receive_cost(src, dest)

    def get_send_cost(self, src, dest):
        """
        The cost of the send operation (e.g. to work to done on the
        sending node) when sending a message to core dest
        """
        return self._get_send_cost(src, dest)

    def get_numa_information(self):
        """
        Return information on NUMA nodes. This is a a list of
        list. Every element of the outer list represents a NUMA node
        and the inner list the cores in that NUMA node.
        """
        return None

    # --------------------------------------------------
    # Helpers
    def get_cores(self):
        """
        Return a list of cores
        """
        return [ c for c in range(self.get_num_cores()) ]

    def output_graph(self):
        """ Write the graph out to disk as <machine_name>_graph
        """
        helpers.output_graph(self.graph, '%s_graph' % self.get_name())

    # --------------------------------------------------
    # Results from evaluation
    def set_evaluation_result(self, ev):
        """
        Save the evaluation result as part of the model. The estimated
        cost should be part of the model

        @param t Result as in evaluate.Result
        """
        self.evaluation = ev

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

    def get_numa_node(self, core1):
        """
        Return all cores that are on the same NUMA node then the given core
        """
        numa_node = []
        for node in self.graph.nodes():
            if self.on_same_numa_node(core1, node):
                numa_node.append(node)
        return numa_node

    def get_numa_id(self, core1):
        """
        Determine NUMA node for the given core
        """
        print helpers.bcolors.WARNING + "Warning: Deprecated: get_numa_id" \
            + helpers.bcolors.ENDC
        return core1 / self.get_cores_per_node()

    # --------------------------------------------------

    def _add_numa(self, graph, node1, node2, cost):
        """
        Wrapper function to add edges between two NUMA nodes.
        """
        n1 = node1*self.get_cores_per_node()
        n2 = node2*self.get_cores_per_node()
        for c1 in range(self.get_cores_per_node()):
            for c2 in range(self.get_cores_per_node()):
                src = (n1+c1)
                dest = (n2+c2)
                if src < dest:
                    logging.info("Adding edge %d -> %d with weight %d" % \
                                     (src, dest, cost))
                    graph.add_edge((src, dest), cost)

    def _connect_numa_nodes(self, g, g_numa, src, ):
        """
        Assuming that routing is taking the shortes path, NOT true on
         e.g. SCC
        """
        self._connect_numa_internal(g, src)
        cost = shortest_path(g_numa, src)[1]
        logging.info("connect numa nodes for %d: cost array size is: %d" % \
                         (src, len(cost)))
        for trg in range(len(cost)):
            if src!=trg:
                self._add_numa(g, src, trg,
                               cost[trg]*self.get_cost_across_numa())

    def _connect_numa_internal(self, graph, numa_node):
        """
        fully connect numa islands!
        """
        for i in range(self.get_cores_per_node()):
            for j in range(self.get_cores_per_node()):
                if j>i:
                    node1 = numa_node*self.get_cores_per_node() + i
                    node2 = numa_node*self.get_cores_per_node() + j
                    graph.add_edge((node1, node2), self.get_cost_within_numa())

    def get_root_node(self):
        return None

    def _parse_receive_result_file(self):
        """
        Parse pairwise receive cost results measure with the UMP receive
        benchmark in the Barrelfish tree.

        We then use these measurements for the receive cost in the simulator

        """
        fname = '%s/%s/pairwise_receive' % \
                (config.MACHINE_DATABASE, self.get_name())
        f = open(fname)
        assert not self.recv_cost
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('(\d+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)', l)
            if m:
                (src, dest, cost, stderr) = (int(m.group(1)),
                                             int(m.group(2)),
                                             float(m.group(3)),
                                             float(m.group(4)))
                assert (src, dest) not in self.recv_cost
                self.recv_cost[(src, dest)] = cost

    def _parse_send_result_file(self):
        """
        Parse pairwise send cost results measure with the UMP send
        benchmark in the Barrelfish tree.

        We then use these measurements for the send cost in the simulator

        """
        fname = '%s/%s/pairwise_send' % \
                (config.MACHINE_DATABASE, self.get_name())
        f = open(fname)
        assert not self.send_cost
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('(\d+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)', l)
            if m:
                (src, dest, cost, stderr) = (int(m.group(1)),
                                             int(m.group(2)),
                                             float(m.group(3)),
                                             float(m.group(4)))
                assert (src, dest) not in self.send_cost
                self.send_cost[(src, dest)] = cost


    def _get_receive_cost(self, src, dest):
        """
        Return the receive cost for a pair (src, dest) of cores

        This is the cost on dest to receive a message from src.

        """
        if (src==dest):
            return 0
        assert (src, dest) in self.recv_cost
        return self.recv_cost[(src, dest)]


    def _get_send_cost(self, src, dest):
        """
        Return the send cost for a pair (src, dest) of cores

        """
        if (src==dest):
            return 0
        assert (src, dest) in self.send_cost
        return self.send_cost[(src, dest)]