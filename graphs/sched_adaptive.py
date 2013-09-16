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
    """
    Scheduler supporting dynamic creation of broadcast tree

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
        @return A list containing all inactive nodes

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
            (self.mod.get_num_numa_hops_for_cores(sending_node, c), c) \
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

        # Remember choice
        if len(inactive_nodes)>0:
            # don't add same node twice
            assert inactive_nodes[0] not in self.store[sending_node]
            self.store[sending_node].append(inactive_nodes[0])
            print self.store[sending_node]

        return inactive_nodes

    def get_final_schedule(self, sending_node, active_nodes=None):
        """
        Return schedule previously found by iterative find_schedule calls. 

        """
        return [(None, s) for (c,s) in self.store[sending_node]]


