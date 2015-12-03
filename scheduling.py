# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import pdb
from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class Scheduling(object):

    def __init__(self, graph):
        """Initializes Scheduling with a graph model

        @param graph An instance of digraph representing the tree
        topology for which to search a model for.
        """
        print "Initializing scheduler with %s" % str(graph)
        self.graph = graph

    def find_schedule(self, sending_node, active_nodes):
        """
        Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @param active_nodes A list of active nodes.
        @return List of neighbors in FIFO order.
        """
        return None

    def get_final_schedule(self, sending_node, active_nodes=None):
        """Get the final schedule. This is equal to what will be returned
        from find_schedule except for adaptive models, that just
        replay what they generated before.

        The restult is a list of tuples (cost, receiver). Each element
        represents one edge used in the topology tree. The elements in
        the list have to be given in the order in which messages
        should be sent to neighbors.

        """
        return self.find_schedule(sending_node, active_nodes)

    def _return_neighbors(self, src):
        """
        Create list of children first, and the cost of the message list

        """
        nb = []
        for dest in self.graph.neighbors(src):
            nb.append((model.edge_weight((src, dest)), dest))
        return nb
