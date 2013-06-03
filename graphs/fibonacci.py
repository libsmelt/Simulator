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

class Fibonacci(overlay.Overlay):
    """
    Build a cluster topology for a model
    """
    
    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        super(Fibonacci, self).__init__(mod)
        self.coordinators = self.get_coordinators()

    def get_name(self):
        return "fibonacci"

    def fibonacci(self, depth):
        g = digraph()
        if depth==1:
            g.add_node(1)
        elif depth==2:
            g.add_node(1)
            g.add_node(2)
            g.add_edge((1,2))
        else:
            g_r = self.fibonacci(depth-1)
            g_l = self.fibonacci(depth-2)
            g.add_node(depth)
            g = algorithms.merge_graphs(g_r, g_l)
    

        
    def _get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph
        """

