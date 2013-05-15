#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Gruyere(numa_model.NUMAModel):

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        g = super(Gruyere, self)._build_graph()
        super(Gruyere, self).__init__(g)

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return "gruyere"

    def get_num_numa_nodes(self):
        return 8

    def get_num_cores(self):
        return 32

    def get_numa_information(self):
        return (
            (0,1,2,3,), 
            (4,5,6,7,), 
            (8,9,10,11,), 
            (12,13,14,15,), 
            (16,17,18,19,), 
            (20,21,22,23,), 
            (24,25,26,27,), 
            (28,29,30,31) 
            )
    # --------------------------------------------------

    def _build_numa_graph(self):
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

        return g_numa
        

