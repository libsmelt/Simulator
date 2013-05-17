#!/usr/bin/env python

import model
import helpers

from pygraph.classes.graph import graph

# --------------------------------------------------
class NUMAModel(model.Model):

    def __init__(self, g):
        super(NUMAModel, self).__init__(g)


    def _build_numa_graph(self):
        return None

    def _build_graph(self):
        """
        Build a graph model for a NUMA machine
        """
        g_numa = self._build_numa_graph()
        helpers.output_graph(g_numa, '%s_numa' % self.get_name())

        gr = graph()
        gr.add_nodes(range(self.get_num_cores()))

        for n in range(self.get_num_numa_nodes()):
            self._connect_numa_nodes(gr, g_numa, n)

        return gr
        

