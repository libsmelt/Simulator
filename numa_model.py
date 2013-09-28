#!/usr/bin/env python

import model
import helpers
import re
import config

from pygraph.classes.graph import graph
from pygraph.algorithms.minmax import shortest_path

# --------------------------------------------------
class NUMAModel(model.Model):

    def __init__(self, g):

        super(NUMAModel, self).__init__(g)

        # Dictionary for receive costs
        # key is (src, dest), value is the cost in cycles/10
        self.recv_cost = {}

        # Dictionary for send costs
        # key is (src, dest), value is the cost in cycles/10
        self.send_cost = {}


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


    def _parse_receive_result_file(self, fname):
        """
        Parse pairwise receive cost results measure with the UMP receive
        benchmark in the Barrelfish tree.

        We then use these measurements for the receive cost in the simulator
        @param f: Handle to results.dat file of UMP receive benchmark

        """
        fname = fname + config.result_suffix()
        f = open(fname)
        assert not self.recv_cost
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('(\d+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)', l)
            if m:
                (src, dest, cost, stderr) = (int(m.group(1)), 
                                             int(m.group(2)),
                                             float(m.group(3)),
                                             float(m.group(4)))
                assert (src, dest) not in self.recv_cost
                self.recv_cost[(src, dest)] = cost

    def _parse_send_result_file(self, fname):
        """
        Parse pairwise send cost results measure with the UMP send
        benchmark in the Barrelfish tree.

        We then use these measurements for the send cost in the simulator
        @param f: Handle to results.dat file of UMP send benchmark

        """
        fname = fname + config.result_suffix()
        f = open(fname)
        assert not self.send_cost
        for l in f.readlines():
            l = l.rstrip()
            m = re.match('(\d+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)', l)
            if m:
                (src, dest, cost, stderr) = (int(m.group(1)), 
                                             int(m.group(2)),
                                             float(m.group(3)),
                                             float(m.group(4)))
                assert (src, dest) not in self.send_cost
                self.send_cost[(src, dest)] = cost


    def _get_receive_cost(self, src, dest):
        """
        Return the receive cost for a pair (src, dest) of cores
        
        """
        if (src==dest):
            return 0
        assert (src, dest) in self.recv_cost
        return self.recv_cost[(src, dest)]


    def _get_send_cost(self, src, dest):
        """
        Return the send cost for a pair (src, dest) of cores
        
        """
        if (src==dest):
            return 0
        assert (src, dest) in self.send_cost
        return self.send_cost[(src, dest)]
