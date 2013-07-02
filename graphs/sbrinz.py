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
        super(Sbrinz, self)._parse_receive_result_file(
            open('measurements/receive_sbrinz'))
        super(Sbrinz, self)._parse_send_result_file(
            open('measurements/send_sbrinz'))

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return "sbrinz"

    def get_send_cost(self, src, dest):
        return super(Sbrinz, self)._get_send_cost(src, dest)

    def get_num_numa_nodes(self):
        return 4

    def get_num_cores(self):
        return 16

    def get_receive_cost(self, src, dest):
        return super(Sbrinz, self)._get_receive_cost(src, dest)
