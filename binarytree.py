# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

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
