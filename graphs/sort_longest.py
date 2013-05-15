# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

import pdb

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# --------------------------------------------------
class SortLongest(scheduling.Scheduling):
    """
    Naive scheduling.

    Send messages in the order encoded in the model.
    """

    def find_schedule(self, sending_node):
        """
        Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @return List of neighbors in FIFO order.
        """
        nb=self.__get_longest_path(sending_node, [])
        nb.sort(key=lambda tup: tup[0], reverse=True)
        return nb

    def __get_longest_path_for_node(self, node, omit, depth):
        """
        Return the length of the longest path starting at the given node
        Note: Graph must not have cycles (is this true?)
        """
        assert not omit == None
        l = 0
        for n in self.graph.neighbors(node):
            if not n in omit: 
                o_ = omit
                o_.append(node)
                ltmp = self.graph.edge_weight((node, n)) + \
                    self.__get_longest_path_for_node(n, o_, depth+1)
                indent = ''
                for i in range(depth):
                    indent += ' '
                print "%sPath length from %d via %d is %d" % (indent, node, n, ltmp)
                l = max(l, ltmp)
        return l

    def __get_longest_path(self, src, omit):
        """
        Return the maximum length for subtrees starting at every node
        given in nblist
        """
        paths = []

        assert not omit == None
        omit.append(src)

        print "=================================================="
        for n in self.graph.neighbors(src):
            if not n in omit:
                m = self.graph.edge_weight((src, n)) + \
                    self.__get_longest_path_for_node(n, omit, 0)
                paths.append((m, n))
        return paths

