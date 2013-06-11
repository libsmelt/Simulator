# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import pdb
import logging
import evaluate

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Model(object):

    evaluation = None

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
        assert self.get_num_numa_nodes() is not None # Should be overriden in childs
        if self.get_num_numa_nodes()>0:
            return self.get_num_cores() / self.get_num_numa_nodes()
        else:
            return self.get_num_cores()

    # Transport cost
    def get_cost_within_numa(self):
        return 1

    def get_cost_across_numa(self):
        return 10

    # Node processing cost
    def get_receive_cost(self, src, dest):
        """
        The cost of receive operations on dest for messages from
        src. This is essentially the time required for the memory read
        in case of a new message, which in turn is the time required
        by the cache-coherency protocol to update the (at this point
        invalid) cache-line in the local cache with the updates
        version in the senders cache.
        """
        return 25

    def get_send_cost(self, src, dest):
        """
        The cost of the send operation (e.g. to work to done on the
        sending node) when sending a message to core dest
        """
        return 25
    
    def get_numa_information(self):
        """
        Return information on NUMA nodes. This is a a list of
        list. Every element of the outer list represents a NUMA node
        and the inner list the cores in that NUMA node.
        """
        return None

    # --------------------------------------------------
    # Results from evaluation
    def set_evaluation_result(self, ev):
        """
        Save the evaluation result as part of the model. The estimated
        cost should be part of the model

        @param t Result as in evaluate.Result
        """
        self.evaluation = ev

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

    def get_numa_id(self, core1):
        """
        Determine NUMA node for the given core
        """
        return core1 / self.get_cores_per_node()
        
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
