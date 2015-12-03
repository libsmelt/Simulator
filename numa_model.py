#!/usr/bin/env python

import model
import helpers
import re
import config

from pygraph.classes.graph import graph
from pygraph.algorithms.minmax import shortest_path

# --------------------------------------------------
class NUMAModel(model.Model):

    # Graph representing the NUMA structure of a machine
    g_numa = None

    def __init__(self, g):

        print helpers.bcolors.WARNING + "Warning: NUMAModel deprecated" + helpers.bcolors.ENDC
        super(NUMAModel, self).__init__(g)


    # --------------------------------------------------

    def _build_numa_graph(self):
        """Build a graph representing the NUMA topology of the machine.

        This graph is used to calculate cost for fully-meshed machine
        model.

        This graph expresses the cost of sending messages between NUMA
        nodes.
        """
        return None


    def _build_graph(self):
        """
        Build a graph model for a NUMA machine
        """
        self.g_numa = self._build_numa_graph()

        if not self.g_numa:
            return

        helpers.output_graph(self.g_numa, '%s_numa' % self.get_name())

        gr = graph()
        gr.add_nodes(range(self.get_num_cores()))

        for n in range(self.get_num_numa_nodes()):
            self._connect_numa_nodes(gr, self.g_numa, n)

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


    def get_numa_information(self):
        return self._auto_generate_numa_information()


    def _build_numa_graph(self):
        """
        Graph of NUMA nodes. This graph is used to calculate cost for
        fully-meshed machine model.

        This graph expresses the cost of sending messages between NUMA
        nodes.
        """
        g_numa = graph()
        g_numa.add_nodes(range(self.get_num_numa_nodes()))

        if self.get_num_numa_nodes() == 4:
            for e in [(0,1), (1,3), (3,2), (2,0)]:
                g_numa.add_edge(e)
        elif self.get_num_numa_nodes() == 2:
            g_numa.add_edge((0,1))
        else:
            raise Exception(('Do not know how to build a NUMA model for a '
                             'machine with %d cores') % self.get_num_numa_nodes())

        helpers.output_graph(g_numa, '%s_numa' % self.get_name());

        return g_numa
