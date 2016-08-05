# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import own code
import helpers
import algorithms
import overlay

class Sequential(overlay.Overlay):
    """
    Build a cluster topology for a model
    """

    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        super(Sequential, self).__init__(mod)

    def get_name(self):
        return "sequential"

    def _get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph
        """

        # Run binary tree algorithm
        sequential = algorithms.sequential(self.mod.get_graph(),
                                           self.mod.get_graph().nodes(),
                                           0)

        # Print graph
        helpers.output_graph(sequential, 'sequential', 'dot')

        return sequential


    def _get_multicast_tree(self, graph):
        """
        Return the broadcast tree as a graph
        """

        # Run binary tree algorithm
        print 'Building sequential multicast', graph.nodes()
        sequential = algorithms.sequential(graph, graph.nodes(), 0)

        return sequential
