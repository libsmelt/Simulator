# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv
import logging

# Import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.readwrite.dot import write
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.minmax import minimal_spanning_tree

# Import own code
import evaluate
import model
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
                                           0)

        # Print graph
        helpers.output_graph(sequential, 'sequential', 'dot')

        return sequential
