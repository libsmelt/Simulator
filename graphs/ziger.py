#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Ziger(numa_model.NUMAModel):

    recv_cost = { 0: 25, 1: 42, 2: 50 }

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

    def get_receive_cost(self, src, dest):
        hops = self.get_num_numa_hops(self.get_numa_id(src), 
                                      self.get_numa_id(dest))
        return self.recv_cost[hops]
