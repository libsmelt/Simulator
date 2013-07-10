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

    def _get_broadcast_tree(self):
        """
        Run MST algorithm
        """
        gr = self.mod.get_graph()
        
        mst = graph()
        mst.add_nodes(gr.nodes())

        mst_edges = minimal_spanning_tree(gr)
        print mst_edges

        for (trg,src) in mst_edges.items():
            if src != None:
                print "Adding edge %s -> %s" % (src, trg)
                mst.add_edge((src, trg)) #, gr.edge_weight((src, trg)))

        return mst
