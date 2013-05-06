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

class Cluster:
    
    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        assert isinstance(mod, model.Model)
        self.mod = mod
        self.coordinators=[]
        for core in range(len(mod.get_graph())):
            new_coordinator = True
            for c in self.coordinators:
                if mod.on_same_numa_node(core, c):
                    new_coordinator = False
            if new_coordinator:
                self.coordinators.append(core)
        print "Coordinator nodes are: %s" % str(self.coordinators)

    def get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph
        """

        # Build NUMA node graph with weights first
        g_numa = graph()
        for c in self.coordinators:
            g_numa.add_node(c)
            for co in self.coordinators:
                if co<c:
                    g_numa.add_edge((c, co),
                                    self.mod.get_graph().edge_weight((c, co)))

        # Print graph
        helpers.output_graph(g_numa, 'cluster_numa', 'dot')

        # Now: find a tree for this graph
        # Observation: Machines today typically don't have more than 8 nodes
        # core 0 sends one message "across" the machine, all others: MST

        # max-hops: 3
        # core 0 histogram (question: why would we start at 0?)
        # - 1 hops: 2
        # - 2 hops: 2
        # - 3 hops: 3
        # core 2 histogram
        # - 1 hops: 4
        # - 2 hops: 2
        # - 3 hops: 1

        # might be able to do some clustering: split up nodes such
        # that half of them are in one cluster afterwards, the the
        # other half in another. Split them up such that the number of
        # links connecting the two clusters is minimal. Trying this
        # bruteforce would require n! / ((n/2)!) I think .. 

        # I think it might be best to cust construct a binary-tree!
        # except for contention
        # but if we send a message far away, with many hops, that is kind of stupid (or is it?)

        g_outer = algorithms.binary_tree(g_numa)

        helpers.output_graph(g_outer, 'cluster_outer_bin', 'dot')
        pdb.set_trace()

        return None
