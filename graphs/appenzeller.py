#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Appenzeller(numa_model.NUMAModel):

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        g = super(Appenzeller, self)._build_graph()
        super(Appenzeller, self).__init__(g)

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return "appenzeller"

    def get_num_numa_nodes(self):
        return 8

    def get_num_cores(self):
        return 6

    def get_numa_information(self):
        g_numa = graph()
        g_numa.add_nodes(range(self.get_num_numa_nodes()))

        d = dict() # 8x4 /2 = 16 links
        d[0] = [1,2,4,5]
        d[1] = [0,3,5,4]
        d[2] = [0,3,6,7]
        d[3] = [2,6,7,1]
        d[4] = [0,1,5,6]
        d[5] = [0,1,4,7]
        d[6] = [2,3,7,4]
        d[7] = [2,3,6,5]

        errors = 0
        for s in range(8):
            for d in d[s]:
                try:
                    g_numa.add_edge((s,d))
                except:
                    errors += 1
                    
        assert errors == 16

        helpers.output_graph(g_numa, 'appenzeller_numa');

        return g_numa
