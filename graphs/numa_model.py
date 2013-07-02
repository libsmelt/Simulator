#!/usr/bin/env python

import model
import helpers
import re

from pygraph.classes.graph import graph
from pygraph.algorithms.minmax import shortest_path

# --------------------------------------------------
class NUMAModel(model.Model):

    def __init__(self, g):
        super(NUMAModel, self).__init__(g)

    # --------------------------------------------------

    def get_num_numa_hops(self, src, dest):
        """
        Get number of NUMA hops for communication between given pair
        of NUMA nodes.
        """
        (tree, hops) = shortest_path(self.g_numa, src)
        return hops.get(dest)

    def get_num_numa_hops_for_cores(self, src, dest):
        """
        Get number of NUMA hops for communication between given pair of cores
        """
        return self.get_num_numa_hops(self.get_numa_id(src),
                                      self.get_numa_id(dest))

    # --------------------------------------------------

    def _build_numa_graph(self):
        return None

    def _build_graph(self):
        """
        Build a graph model for a NUMA machine
        """
        self.g_numa = self._build_numa_graph()
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

    def _parse_receive_result_file(self, f):
        """
        Parse pairwise receive cost results measure with the UMP receive
        benchmark in the Barrelfish tree.

        We then use these measurements for the receive cost in the simulator
        @param f: Handle to results.dat file of UMP latency benchmark
        """
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('\d+\s+\d+\s+[0-9.]+\s+[0-9.]+', l)
            if m:
                print l
        
        

