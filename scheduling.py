#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

# --------------------------------------------------
class Scheduling(object):

    def __init__(self, graph):
        """Initializes Scheduling with a graph model

        @param graph An instance of digraph representing the tree
        topology for which to search a model for.
        """
        print "Initializing scheduler %s with %s" % (str(self), str(graph))
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

    def _return_neighbors(self, src, active_nodes):
        """
        Create list of children first, and the cost of the message list

        @param active_nodes List of already active nodes, ignore these.
        """
        exclude = active_nodes if active_nodes != None else []
        nb = []
        for dest in self.graph.neighbors(src):
            if not dest in exclude:
                nb.append((self.graph.edge_weight((src, dest)), dest))
        return nb

    def next_eval(self):
        """Evaluation reached next protocol.

        This is important for dynamic schedulers, such as the adaptive
        tree, to signal that the tree has been completly generated.
        """

    def visualize(self, model, topo):
        return None

    def assert_history(self):
        return True
