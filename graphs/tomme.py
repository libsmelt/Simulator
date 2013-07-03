#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Tomme(numa_model.NUMAModel):
# http://ark.intel.com/products/40201/Intel-Xeon-Processor-L5520-8M-Cache-2_26-GHz-5_86-GTs-Intel-QPI

    def __init__(self):
        """
        Build the model and use it to initialize the Model superclass
        """
        g = super(Tomme, self)._build_graph()
        super(Tomme, self).__init__(g)
        super(Tomme, self)._parse_receive_result_file(
            open('measurements/receive_%s' % self.get_name()))
        super(Tomme, self)._parse_send_result_file(
            open('measurements/send_%s' % self.get_name()))

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return "tomme"

    def get_num_numa_nodes(self):
        return 2

    def get_num_cores(self):
        return 16

    def get_send_cost(self, src, dest):
        return super(Tomme, self)._get_send_cost(src, dest)

    def get_receive_cost(self, src, dest):
        return super(Tomme, self)._get_receive_cost(src, dest)
