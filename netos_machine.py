#!/usr/bin/env python

import os
import sys

import model
import config
import topology_parser
import itertools
import gzip
from multimessage import MultiMessage

from pygraph.classes.digraph import digraph

# --------------------------------------------------
# NetOS base class
class NetosMachine(model.Model):
    """A machine model that parses the NetOS machine database for machines

    We intentionally did not use the NUMA model as a base class, which
    was meant as a dirty hack to auto-generate the graph for a
    machine. We can now (and should) do this directly from the
    pairwise measurements.

    Note: Currently this inherits from Model, but it should really
    not. The initialization here is completely separate from the base
    classes init code.


    We currently also parse hierarchical information from various
    Linux tools (lscpu, likwid). This is useful for hierarchical
    models (such as clusters), but also virtualization.

    """

    # Topology information as returned by the topology_parser
    res = None

    # Machine name
    name = None

    def __init__(self):
        """Initialize the Simulator for a NetOS machine.

        Read topology information from the NetOS machine DB and build
        a fully-connected graph representing the pairwise
        message-passing communication cost (as a sum of send and
        receive cost).

        """
        self.name = config.args.machine
        print 'Initializing NetOS machine %s' % self.name

        # Build a graph model
        super(NetosMachine, self).__init__()

        # Read multimessage data
        fname = '%s/%s/multimessage.gz' % \
                (config.MACHINE_DATABASE, self.get_name())

        self.mm = None
        try:
            f = gzip.open(fname, 'r')
            self.mm = MultiMessage(f)
            f.close()
        except IOError:
            print 'No multimessage data for this machine'
        except:
            raise

        self.send_history = {}
        self.reset()

    def reset(self):
        ## XXX Also need to reset send history on an individual node
        ## for barriers etc, when reverting from reduction to ab
        if self.send_history:
            print 'Resetting send history', self.send_history
        self.send_history = {}


    def get_num_numa_nodes(self):
        """Get the number of NUMA nodes
        """
        return len(self.machine_topology['NUMA'].get())

    def get_cores_per_node(self):
        """Deprecated: This should ONLY be used for visualization purposes,
        and never for actually generating the model (use pairwise
        measurements for that)


        Assumptions: All NUMA nodes have the same number of cores.
        """
        return len(self.machine_topology['NUMA'].get()[0])

    def get_numa_information(self):
        return self.machine_topology['NUMA'].get()


    def get_numa_node_by_id(self, nidx):
        """Get all cores on the given NUMA node
        """
        return self.machine_topology['NUMA'].get()[nidx]


    def get_numa_id(self, c):
        """ Return the ID of the NUMA node of core c
        """

        nidx = -1
        for nodes in self.machine_topology['NUMA']:
            nidx += 1
            if c in nodes:
               return nidx


    def get_num_cores(self):
        return self.machine_topology['numcpus']

    def get_name(self):
        return self.name

    def get_cores(self, only_active=False):
        c = list(itertools.chain.from_iterable(self.machine_topology['NUMA'].get()))
        c = self.filter_active_cores(c, only_active)
        return c

    def _build_graph(self):
        """Build a graph representing the communication cost within that
        machine.

        The cost of communication for each pair of cores is the
        send_cost + receive_cost on that link.

        """

        _c_list = self.get_cores()

        # Add all cores to the graph
        gr = digraph()
        gr.add_nodes(_c_list)

        for snd in _c_list:
            for rcv in _c_list:
                if snd!=rcv:
                    snd_cost = self._get_send_cost(snd, rcv)
                    rcv_cost = self._get_receive_cost(snd, rcv)
                    gr.add_edge((snd, rcv), snd_cost + rcv_cost)

        return gr


    def get_numa_id(self, core1):
        """Determine ID of the NUMA node <core1> resides on.
        """
        nodes = self.machine_topology['NUMA'].get()
        for (n, i) in zip(nodes, range(len(nodes))):
            if core1 in n:
                return i


    def query_send_cost(self, src, dest, batchsize=1):
        """In difference to get_send_cost, query_send_cost just retrieves the
        send cost without adding the message to the history.

        """
        return self._get_send_cost(src, dest, batchsize)


    def get_send_cost(self, src, dest, batchsize=1):

        """
        The cost of the send operation (e.g. to work to done on the
        sending node) when sending a message to core dest
        """
        l = self.get_numa_id(src) == self.get_numa_id(dest)
        _send_history = self.send_history.get(src, [])
        num_l = len([ b for b in _send_history if b ])
        num_r = len([ b for b in _send_history if not b ])

        _factor = 1.0
        if self.mm:
            _factor = self.mm.get_factor(num_r, num_l, l)

        print 'Factor is', _factor

        self.send_history[src] = _send_history + [l]
        return self._get_send_cost(src, dest, batchsize)*_factor


    def __repr__(self):
        return self.name


# --------------------------------------------------
# Static function
def get_list():
    """Get list of NetOS machines
    """

    sys.path.append(config.MACHINE_DATABASE)
    from machineinfo import machines

    return [ s for (s, _, _) in machines ]
