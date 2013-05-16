# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
import Queue
import logging

def binary_tree(m, nodes=[], out_degree=2):
    """
    Construct a binary tree for the given g
    XXX Currently, this works only for out_degree=2

    @type m: graph
    @param m: The machine model. The weights for the edges in the binary_tree
        will be extracted from the model

    @type nodes: list
    @param nodes: list of nodes to build a binary tree for. If list is
        empty, it will default to m.nodes()

    @type out_degree: number
    @param out_degree: outdegree of nodes in the generated graph. Currently,
        this is ignored
    """
    assert(len(m.nodes())>0) # graph has nodes

    g = graph()
    if len(nodes)==0:
        nodes = m.nodes()
    num = len(nodes)

    for n in nodes:
        g.add_node(n)
    
    for i in range(num):
        p = 2*(i+1)-1
        pp = 2*(i+1)
        if p < num:
            g.add_edge((nodes[i],  nodes[p]), \
                           m.edge_weight((nodes[i], nodes[p])))
            if pp < num:
                g.add_edge((nodes[i], nodes[pp]), \
                               m.edge_weight((nodes[i], nodes[pp])))

    return g

def simple_tree(m, nodes, coordinator):
    """
    Construct a simple two-level tree. The coordinator is the root, and all 
    the other nodes are its children

    @type m: graph
    @param m: The machine model. The weights for the edges in the binary_tree
        will be extracted from the model

    @type nodes: list
    @param nodes: list of nodes to build a tree for. If list is
        empty, it will default to m.nodes()

    @type coordinator: number
    @param coordinator: This node will be the root of the tree
    """
    assert(len(m.nodes())>0) # graph has nodes

    g = graph()
    g.add_node(coordinator)

    for n in nodes:
        if n != coordinator:
            g.add_node(n)
            g.add_edge((n, coordinator), \
                           m.edge_weight((n, coordinator)))
    return g

def merge_graphs(g1, g2):
    """
    Merge two graphs to a new graph (V, E) with V = g1.nodes \union g2.nodes
    and Edge e \in g1 or e \in g2 -> e \in E.
    """
    if g1.DIRECTED or g2.DIRECTED:
        g = digraph()
    else:
        g = graph()

    for n in g1.nodes():
        g.add_node(n)
    for n in g2.nodes():
        if not n in g.nodes():
            g.add_node(n)
    for e in g1.edges():
        try: 
            g.add_edge(e, g1.edge_weight(e))
        except:
            logging.info("merge_graphs: adding edge %d %d" % (e[0], e[1]))
    for e in g2.edges():
        try: 
            g.add_edge(e, g2.edge_weight(e))
        except:
            logging.info("merge_graphs: adding edge %d %d" % (e[0], e[1]))
    return g

    

            
        
    
