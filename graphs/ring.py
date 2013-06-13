# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv

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

class Ring(overlay.Overlay):
    """
    Build a ring topology for a model
    
    The outer topology is going to be a ring. We need a directed graph
    to represent the model here, while previously, a undirected graph
    would work as well and we would just not send messages from where
    we received them from.
    """
    
    def __init__(self, mod):
        """
        Initialize the ring algorithm
        """
        # if mod.get_num_cores()!=32:
        #     raise Exception('Rings only supported on machines with 32 cores')
        super(Ring, self).__init__(mod)

    def get_name(self):
        return "ring"

    def _get_broadcast_tree(self):
        """
        This currently only works for 8x4x1 model
        """
        
        # Sanity check. Is the model an 8x4x1 model?
        assert(len(self.mod.get_graph().nodes())==32)
        for i in range(32):
            assert (i in self.mod.get_graph().nodes())

        g = self._get_outer_rings()
        for i in [0, 4, 8, 12, 16, 20, 24, 28]:
            numa_node = self.mod.get_numa_node(i)
            g = algorithms.merge_graphs(algorithms.simple_tree(\
                    self.mod.get_graph(), numa_node, i), g)

        helpers.output_graph(g, 'ring', 'neato')
        return g

    def get_root_node(self):
        return 8

    def _get_outer_rings(self):
        """
        Get rings connecting the NUMA nodes
        """
        g = digraph()
        for i in [0, 4, 8, 12, 16, 20, 24, 28]:
            g.add_node(i)

        for e in [(8,12),\
                      (12,28),\
                      (28,24),\
                      (24,8),\
                      (8,4),\
                      (4,0),\
                      (0,16),\
                      (16,20),\
                      (20,8)]:
            g.add_edge(e, self.mod.get_graph().edge_weight(e))

        return g    
