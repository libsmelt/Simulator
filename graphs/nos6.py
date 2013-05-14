#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Nos(numa_model.NUMAModel):

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        g = super(Nos, self)._build_graph()
        super(Nos, self).__init__(g)

    # --------------------------------------------------
    # Characteritics of model
    def get_num_numa_nodes(self):
        return 2

    def get_num_cores(self):
        return 4

    def get_numa_information(self):
        return ( 
            (0, 1), 
            (2, 3)
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
        g_numa.add_edge((0,1))

        return g_numa
