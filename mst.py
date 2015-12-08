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
from pygraph.algorithms.minmax import minimal_spanning_tree
from pygraph.classes.graph import graph

# Import own code
import overlay

class Mst(overlay.Overlay):
    """
    Build overlay based on minimum spanning tree

    Problems with this are:
    - parallelism not considered, resulting graph could be a path

    """
    
    def __init__(self, mod):
        """
        Initialize the clustering algorithm

        """
        super(Mst, self).__init__(mod)
        

    def get_name(self):
        return "mst"


    def _build_tree(self, g):
        """
        Iteratively run minimum spanning tree algorithm on graph
        
        """
        # Init graph and add nodes
        mst = digraph()
        mst.add_nodes(g.nodes())

        # Get a dictionary representing the spanning tree. From
        # looking at the code, the dictionary encodes for each node,
        # where the edge that connects it with the root is coming
        # from.
        mst_edges = minimal_spanning_tree(g, self.get_root_node())
        print 'Minumum spanning tree:', mst_edges

        for (r, s) in mst_edges.items():

            # In case of the root
            if s == None:
                continue

            # Otherwise, r is reached via s
            mst.add_edge((s,r)) # , g.edge_weight((s,r)))
        
        return mst
