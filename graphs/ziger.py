#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Ziger(numa_model.NUMAModel):

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        g = super(Ziger, self)._build_graph()
        super(Ziger, self).__init__(g)

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return "ziger"

    def get_num_numa_nodes(self):
        return 4

    def get_num_cores(self):
        return 24

    def get_numa_information(self):
        return super(Ziger, self)._auto_generate_numa_information()