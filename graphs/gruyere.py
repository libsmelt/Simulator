#!/usr/bin/env python

import model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Gruyere(model.Model):

    # Definition of NUMA topology
    numa = ( 
        (0,1,2,3,), 
        (4,5,6,7,), 
        (8,9,10,11,), 
        (12,13,14,15,), 
        (16,17,18,19,), 
        (20,21,22,23,), 
        (24,25,26,27,), 
        (28,29,30,31) 
        )

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        super(Gruyere, self).__init__(self.__build_graph())

    def get_num_numa_nodes(self):
        return 8

    def get_num_cores(self):
        return 32

    def __build_numa_graph(self):
        """
        Graph of NUMA nodes. This graph is used to calculate cost for
        fully-meshed machine model.

        This graph expresses the cost of sending messages between NUMA
        nodes.
        """
        g_numa = graph()
        g_numa.add_nodes(range(self.get_num_numa_nodes()))

        for i in range(3):
            g_numa.add_edge((i, i+1)) # to right, top row
            g_numa.add_edge((i, i+4)) # top to bottom row

        for i in range(4,7):
            g_numa.add_edge((i, i+1)) # to right, bottom row

        # remainig edges
        g_numa.add_edge((2,7))
        g_numa.add_edge((3,6))
        g_numa.add_edge((3,7))

        # Debug output
        helpers.output_graph(g_numa, 'g_numa_tmp')

        return g_numa

    def __build_graph(self):
        """
        Build a gruyere-like graph model
        """
        g_numa = self.__build_numa_graph()

        gr = graph()
        gr.add_nodes(range(self.get_num_cores()))

        for n in range(self.get_num_numa_nodes()):
            self._connect_numa_nodes(gr, g_numa, n)

        return gr

    def on_same_numa_node(self, core1, core2):
        """
        Return whether two nodes are in the same NUMA region
        """
        for node in self.numa:
            if core1 in node:
                return core2 in node
        pdb.set_trace()
        return None
        

