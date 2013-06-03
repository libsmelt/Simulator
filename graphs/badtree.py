# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv
import logging

# Import pygraph
from pygraph.classes.digraph import digraph
from minmax_degree import minimal_spanning_tree # own minimum spanning tree implementation

# Import own code
import evaluate
import model
import helpers
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

    def _get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph
        """

        # Invert weights
        g_inv = algorithms.invert_weights(self.mod.get_graph())

        # Run binary tree algorithm
        mst_inv = minimal_spanning_tree(g_inv)

        # Build a new graph
        badtree = digraph()
        for n in self.mod.get_graph().nodes():
            badtree.add_node(n)
        print mst_inv.items()
        for (e,s) in mst_inv.items():
            if s != None:
                print "%s %s" % (s,e)
                badtree.add_edge((s, e), # weights from original (non-inverted) graph
                                 self.mod.get_graph().edge_weight((s, e)))

        # Print graph
        helpers.output_graph(badtree, 'badtree', 'dot')

        return badtree
