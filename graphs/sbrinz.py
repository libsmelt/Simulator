#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Sbrinz(numa_model.NUMAModel):

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        g = super(Sbrinz, self)._build_graph()
        super(Sbrinz, self).__init__(g)

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return "sbrinz"

    def get_num_numa_nodes(self):
        return 4

    def get_num_cores(self):
        return 16

    def get_numa_information(self):
        return super(Sbrinz, self)._auto_generate_numa_information()
