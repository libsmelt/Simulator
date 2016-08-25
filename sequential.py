#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

# Import own code
import helpers
import algorithms
import overlay

class Sequential(overlay.Overlay):
    """
    Build a cluster topology for a model
    """

    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        super(Sequential, self).__init__(mod)

    def get_name(self):
        return "sequential"

    def _get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph
        """

        # Run binary tree algorithm
        sequential = algorithms.sequential(self.mod.get_graph(),
                                           self.mod.get_graph().nodes(),
                                           self.get_root_node())

        # Print graph
        helpers.output_graph(sequential, 'sequential', 'dot')

        return sequential


    def _get_multicast_tree(self, graph):
        """
        Return the broadcast tree as a graph
        """

        # Run binary tree algorithm
        print 'Building sequential multicast', graph.nodes()
        sequential = algorithms.sequential(graph, graph.nodes(),
                                           self.get_root_node())

        return sequential
