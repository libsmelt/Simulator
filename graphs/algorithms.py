# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

from pygraph.classes.graph import graph
import Queue

def binary_tree(model, out_degree=2):
    """
    Construct a binary tree for the given g
    """
    assert(len(model.nodes())>0) # graph has nodes

    g = graph()
    nodes = model.nodes()
    num = len(nodes)

    for n in nodes:
        g.add_node(n)
    
    for i in range(num):
        p = 2*(i+1)-1
        pp = 2*(i+1)
        if p < num:
            g.add_edge((nodes[i],  nodes[p]))
            if pp < num:
                g.add_edge((nodes[i], nodes[pp]))

    return g
            
        
    
