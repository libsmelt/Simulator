# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

import pdb
import logging

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

SORT_SUBTREE=True

# --------------------------------------------------
class SortLongest(scheduling.Scheduling):
    """
    Naive scheduling.

    Send messages in the order encoded in the model.
    """
    def __search(self, n1, n2):
        """Sort function used to sort by edge cost

        Sort by the cost first, if the costs are identical, sort by
        the neighbor's node ID.

        """
        res = cmp(n1[0], n2[0])
        if res == 0:
            return -1*cmp(n1[1], n2[1])
        else:
            return -1*res


    def find_schedule(self, sending_node, active_nodes=None):
        """Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @return List of neighbors in FIFO order.
        """
        if SORT_SUBTREE:
            nb=self.__get_longest_path(sending_node, [])
            nb.sort(self.__search)
        else:
            nb=self.__sort_edge_weight(sending_node, active_nodes)
            nb.sort(self.__search, reverse=True)
        return nb


    def __sort_edge_weight(self, src, active_nodes):
        """Sort the nodes by edge weight, rather than the cost of the entire
        subtree.

        """
        out = []
        omit = active_nodes if active_nodes != None else []
        for nb in self.graph.neighbors(src):
            if not nb in omit:
                cost = self.graph.edge_weight((src, nb))
                out.append((cost, nb))
        return out


    def __get_longest_path_for_node(self, node, omit, depth):
        """Return the length of the longest path starting at the given node
        Note: Graph must not have cycles (is this true?)
        """
        assert not omit == None
        l = 0
        for n in self.graph.neighbors(node):   ## node -> n
            if not n in omit:
                o_ = omit
                o_.append(node)
                c1 = self.graph.edge_weight((node, n))
                c2 = self.__get_longest_path_for_node(n, o_, depth+1)
                ltmp = c1 + c2
                indent = ''
                for i in range(depth):
                    indent += ' '
                logging.info("%sPath length from %s via %s is %d (%d + %d)" %
                             (indent, node, n, ltmp, c1, c2))
                l = max(l, ltmp)
        return l


    def __get_longest_path(self, src, omit):
        """Return the maximum length for subtrees starting at every node
        given in nblist
        """
        paths = []

        assert not omit == None
        omit.append(src)

        assert src in self.graph.nodes()

        for n in self.graph.neighbors(src): ## src -> n
            if not n in omit:
                m = self.graph.edge_weight((src, n)) + \
                    self.__get_longest_path_for_node(n, omit, 0)
                paths.append((m, n))
        return paths
