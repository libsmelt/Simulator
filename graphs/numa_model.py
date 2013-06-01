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

    def _auto_generate_numa_information(self):
        res = []
        l = []
        for c in range(self.get_num_cores()):
            if c % self.get_cores_per_node() == 0: 
                if len(l)>0:
                    res.append(l)
                l = []
            l.append(c)
        assert len(l)>0
        res.append(l)
        return res


    def _build_numa_graph(self):
        """
        Graph of NUMA nodes. This graph is used to calculate cost for
        fully-meshed machine model.

        This graph expresses the cost of sending messages between NUMA
        nodes.
        """
        g_numa = graph()
        g_numa.add_nodes(range(self.get_num_numa_nodes()))
        for n in range(self.get_num_numa_nodes()):
            g_numa.add_edge((n, (n+1) % self.get_num_numa_nodes()))

        helpers.output_graph(g_numa, '%s_numa' % self.get_name());

        return g_numa


        

