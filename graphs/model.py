# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import pdb
import logging

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Model(object):

    def __init__(self, graph):
        """
        We initialize models with the graph
        """
        self.graph = graph

    # --------------------------------------------------
    # Characteritics of model
    def get_name(self):
        return None

    def get_num_numa_nodes(self):
        return None

    def get_num_cores(self):
        return None

    def get_cores_per_node(self):
        return self.get_num_cores() / self.get_num_numa_nodes()

    def get_cost_within_numa(self):
        return 1

    def get_cost_across_numa(self):
        return 10
    
    def get_numa_information(self):
        """
        Return information on NUMA nodes. This is a a list of
        list. Every element of the outer list represents a NUMA node
        and the inner list the cores in that NUMA node.
        """
        return None

    # --------------------------------------------------
    # Methods used for building overlay + scheduling
    def get_graph(self):
        return self.graph

    def on_same_numa_node(self, core1, core2):
        """
        Return whether two nodes are in the same NUMA region
        """
        for node in self.get_numa_information():
            if core1 in node:
                return core2 in node
        return None

    def get_numa_node(self, core1):
        """
        Return all cores that are on the same NUMA node then the given core
        """
        numa_node = []
        for node in self.graph.nodes():
            if self.on_same_numa_node(core1, node):
                numa_node.append(node)
        return numa_node
        
    # --------------------------------------------------

    def _add_numa(self, graph, node1, node2, cost):
        """
        Wrapper function to add edges between two NUMA nodes. 
        """
        n1 = node1*self.get_cores_per_node()
        n2 = node2*self.get_cores_per_node()
        for c1 in range(self.get_cores_per_node()):
            for c2 in range(self.get_cores_per_node()):
                src = (n1+c1)
                dest = (n2+c2)
                if src < dest:
                    logging.info("Adding edge %d -> %d with weight %d" % \
                                     (src, dest, cost))
                    graph.add_edge((src, dest), cost)

    def _connect_numa_nodes(self, g, g_numa, src, ):
        """
        Assuming that routing is taking the shortes path, NOT true on
         e.g. SCC
        """
        self._connect_numa_internal(g, src)
        cost = shortest_path(g_numa, src)[1]
        print "connect numa nodes for %d: cost array size is: %d" % \
            (src, len(cost))
        for trg in range(len(cost)):
            if src!=trg:
                self._add_numa(g, src, trg, 
                               cost[trg]*self.get_cost_across_numa())

    def _connect_numa_internal(self, graph, numa_node):
        """
        fully connect numa islands!
        """
        for i in range(self.get_cores_per_node()):
            for j in range(self.get_cores_per_node()):
                if j>i:
                    node1 = numa_node*self.get_cores_per_node() + i
                    node2 = numa_node*self.get_cores_per_node() + j
                    graph.add_edge((node1, node2), self.get_cost_within_numa())
