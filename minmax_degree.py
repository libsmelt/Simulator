#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

# Minimal spanning tree
# This is based on original maxmin implementation of the python-graph project.
# See https://code.google.com/p/python-graph/source/browse/trunk/core/pygraph/algorithms/minmax.py

def minimal_spanning_tree(graph, root):
    """
    Minimal spanning tree.

    @attention: Minimal spanning tree is meaningful only for weighted graphs.

    @type  graph: graph
    @param graph: Graph.

    @type  root: node
    @param root: Optional root node (will explore only root's connected component)

    @rtype:  dictionary
    @return: Generated spanning tree.
    """
    visited = []            # List for marking visited and non-visited nodes
    spanning_tree = {}        # MInimal Spanning tree
    d = dict()

    # Initialization
    visited.append(root)
    nroot = root
    spanning_tree[root] = None

    # Algorithm loop
    while (nroot is not None):
        ledge = _lightest_edge(graph, visited, d)
        if (ledge == (-1, -1)):
            if (root is not None):
                break
            nroot = _first_unvisited(graph, visited)
            if (nroot is not None):
                spanning_tree[nroot] = None
            visited.append(nroot)
        else:
            spanning_tree[ledge[1]] = ledge[0]
            visited.append(ledge[1])
            if ledge[0] in d:
                d[ledge[0]] += 1
            else:
                d[ledge[0]] = 1

    return spanning_tree


def _first_unvisited(graph, visited):
    """
    Return first unvisited node.

    @type  graph: graph
    @param graph: Graph.

    @type  visited: list
    @param visited: List of nodes.

    @rtype:  node
    @return: First unvisited node.
    """
    for each in graph:
        if (each not in visited):
            return each
    return None


def _lightest_edge(graph, visited, d):
    """
    Return the lightest edge in graph going from a visited node to an unvisited one.

    @type  graph: graph
    @param graph: Graph.

    @type  visited: list
    @param visited: List of nodes.

    @type d: Dictionary for remembering the out-degree of every edge.
    @param d: Dictionary

    @rtype:  tuple
    @return: Lightest edge in graph going from a visited node to an unvisited one.
    """
    lightest_edge = (-1, -1)
    weight = -1
    for each in visited:
        if not each in d or d[each]<2:
            for other in graph[each]:
                if (other not in visited):
                    w = graph.edge_weight((each, other))
                    if (w < weight or weight < 0):
                        lightest_edge = (each, other)
                        weight = w
    return lightest_edge
