#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

# Import own code
import algorithms
import overlay

class BinaryTree(overlay.Overlay):
    """
    Build a cluster topology for a model

    """
    def __init__(self, mod):
        """
        Initialize the clustering algorithm

        """
        super(BinaryTree, self).__init__(mod)

    def get_name(self):
        return "binarytree"

    def _get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph

        """
        return self.get_bintree(self.mod.get_graph())

    def _get_multicast_tree(self, graph):
        """
        Run on given multicast tree

        """
        return self.get_bintree(graph)


    def get_bintree(self, graph):
        """
        Generate a binary tree for the given graph.

        """
        bintree = algorithms.binary_tree(graph)

        return bintree
