# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

import pdb
import logging
import random
import model

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class SchedAdaptive(scheduling.Scheduling):
    """Scheduler supporting dynamic creation of broadcast tree
    """

    """I think this stores all outgoing connections (s, r) for each node,
    that are used in the schedule
    """
    store = dict()

    def __init__(self, graph, mod):
        assert isinstance(mod, model.Model)
        self.mod = mod
        self.store = {key: [] for key in range(self.mod.get_num_cores())}
        super(SchedAdaptive, self).__init__(graph)

    def _numa_domain_active(self, core, nodes_active):
        """
        Return whether at least one of the cores of the given NUMA
        domain is active

        """
        for c in self.mod.get_numa_node(core):
            if c in nodes_active:
                return True
        return False


    def find_schedule(self, sending_node, active_nodes=None):
        """
        Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @param active_nodes List of active nodes
        @return A list containing all inactive nodes sorted by cost

        """
        assert active_nodes is not None

        # Find cores that ...
        # Principles are:
        # * The filter makes sure that we do _not_ send unnecessary messages
        #     across NUMA domains
        # * Send expensive messages first
        cores = self.graph.nodes()
        inactive_nodes = [
            # build (cost, core) tuple
            (self.mod.get_send_cost(sending_node, c), c) \
                for c in cores if (
                    # .. are on a NUMA node that is inactive
                    not self._numa_domain_active(c, active_nodes) or
                    # .. or on the same NUMA node
                    self.mod.on_same_numa_node(sending_node, c)
                    # IGNORE: ourself and active nodes
                    ) and c != sending_node and c not in active_nodes
            ]

        print "inactive_nodes from %d with cost: %s" % \
            (sending_node, inactive_nodes)

        # Prefer expensive links
        inactive_nodes.sort(key=lambda tup: tup[0], reverse=True)

        if len(inactive_nodes)==0:
            return []

        # Return only one node
        (next_s, next_r) = inactive_nodes[0]

        # Replace target core (which is the most expensive node in
        # the system), with the cheapest on that node

        # Assumption: fully-connected model

        # All nodes on receivers node
        c_all = self.mod.get_numa_node(next_r)
        c_cost = [ (r, self.mode.get_send_cost(next_s, r)) for r in c_all ]

        # Sort, cheapest node first
        c_cost.sort(key=lambda tup: tup[1])

        # Pick first
        next_hop = [(next_s, c_cost[0][0])]

        # Remember choice
        assert next_hop not in self.store[sending_node] # same node
        self.store[sending_node].append(next_hop)
        print self.store[sending_node]

        return next_hop


    def get_final_schedule(self, sending_node, active_nodes=None):
        """
        Return schedule previously found by iterative find_schedule calls.

        """
        return [(None, s) for (c,s) in self.store[sending_node]]
