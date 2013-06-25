#!/usr/bin/env python

import model
import numa_model
import helpers
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Sbrinz(numa_model.NUMAModel):

    # From: ../results/ds_ump_receive-existing-sbrinz2-20130621-135817/results.dat
    # Note: the cost for accessing a one-hop node not uniform (but we keep it simple)
    recv_cost = { 0: 10, 1: 30, 2: 47 }

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

    # From: ../results/ds_ump_send-existing-sbrinz2-20130621-135420/results.dat
    def get_send_cost(self, src, dest):
        return 26

    def get_num_numa_nodes(self):
        return 4

    def get_num_cores(self):
        return 16

    def get_receive_cost(self, src, dest):
        hops = self.get_num_numa_hops(self.get_numa_id(src), 
                                      self.get_numa_id(dest))
        return self.recv_cost[hops]
