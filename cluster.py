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
from algorithms import binary_tree, sequential, merge_graphs
import overlay

class Cluster(overlay.Overlay):
    """
    Build a cluster topology for a model

    """
    
    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        super(Cluster, self).__init__(mod)
        
    def get_name(self):
        return "cluster"

    def _build_tree(self, g):
        """
        Algorithm to build the cluster tree.
        This algorithm uses the list of coordinators for :py:func:`overlay.get_coordinators`

        :param graph g: Graph for which to build the cluster tree.

        """

        print '--------------------------------------------------'
        print '-- BUILD CLUSTER TOPLOGY'
        print '--------------------------------------------------'

        coords = self.get_coordinators()

        # Build NUMA node graph with weights first
        g_numa = digraph()
        for c in coords:
            g_numa.add_node(c)
            for co in coords:
                if co<c:
                    weight = self.mod.get_graph().edge_weight((c, co))
                    g_numa.add_edge((c, co), weight)
                    g_numa.add_edge((co, c), weight)
                    logging.info(("Adding edge to NUMA node %d %d, "
                                  "with weight %d") % (c, co, weight))

        # Print graph
        helpers.output_graph(g_numa, 'cluster_numa', 'dot')

        # Outer NUMA graph
        g_outer = binary_tree(g_numa)

        for c in self.get_coordinators():
            numa_node = [ n for n in self.mod.get_numa_node(c) if n in g.nodes() ]
            g_simple = sequential(self.mod.get_graph(), numa_node, c)
            g_outer = merge_graphs(g_outer, g_simple)
            print "%s" % str(numa_node)

        helpers.output_graph(g_outer, 'cluster_outer_bin', 'neato')
        return g_outer
