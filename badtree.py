#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

# Import pygraph
from pygraph.classes.digraph import digraph
from minmax_degree import minimal_spanning_tree # own minimum spanning tree implementation

import algorithms
import overlay

class BadTree(overlay.Overlay):
    """
    Build a bad tree.

    We use this to show that picking the "right" topology matters.

    The idea is to invert the weights and run an MST. The spanning
    tree will then be composed of many expensive links
    (i.e. cross-NUMA links).
    """

    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        super(BadTree, self).__init__(mod)

    def get_name(self):
        return "badtree"

    def _build_tree(self, g):
        """
        We build a bad tree by inverting all edge weights and running
        an MST algorithm on the resulting graph.

        """
        # Build graph with inverted edges
        g_inv = algorithms.invert_weights(g)

        # Run binary tree algorithm
        mst_inv = minimal_spanning_tree(g_inv)

        # Build a new graph
        badtree = digraph()

        # Add nodes
        for n in g.nodes():
            badtree.add_node(n)

        # Add edges, copy weights from non-inverted graph
        for (e,s) in mst_inv.items():
            if s != None:
                badtree.add_edge((s, e), g.edge_weight((s, e)))

        return badtree
