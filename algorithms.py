# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
import logging

def binary_tree(m, nodes=[]):
    """
    Construct a binary tree for the given g
    XXX Currently, this works only for out_degree=2

    @type m: graph
    @param m: The machine model. The weights for the edges in the binary_tree
        will be extracted from the model

    @type nodes: list
    @param nodes: list of nodes to build a binary tree for. If list is
        empty, it will default to m.nodes()

    @return g digraph storing the binary graph
    """
    assert(len(m.nodes())>0) # graph has nodes

    g = digraph()
    if len(nodes)==0:
        nodes = m.nodes()
    num = len(nodes)

    # Adding nodes
    # --------------------------------------------------
    for n in nodes:
        g.add_node(n)

    # Adding edges
    # --------------------------------------------------
    for i in range(num):
        p = 2*(i+1)-1
        pp = 2*(i+1)

        # ------------------------------
        if p < num:
            e = (nodes[i], nodes[p])
            assert e in m.edges()
            g.add_edge(e)
            g.set_edge_weight(e, m.edge_weight(e))
            assert (m.edge_weight(e))>1

            # ------------------------------
            if pp < num:
                assert e in m.edges()
                e = (nodes[i], nodes[pp])
                g.add_edge(e)
                g.set_edge_weight(e, m.edge_weight(e))

    return g


def sequential(m, nodes, coordinator):
    """
    Construct a simple two-level tree. The coordinator is the root, and all
    the other nodes are its children.

    The weights of edges are taken from m.

    @type m: graph
    @param m: The machine model. The weights for the edges in the binary_tree
        will be extracted from the model.

    @type nodes: list
    @param nodes: list of nodes to build a tree for. If list is
        empty, it will default to m.nodes()

    @type coordinator: number
    @param coordinator: This node will be the root of the tree

    @return digraph
    """
    assert(len(m.nodes())>0) # graph has nodes

    g = digraph()
    g.add_node(coordinator)

    for n in nodes:
        if n != coordinator:
            g.add_node(n)
            g.add_edge((coordinator, n), \
                           m.edge_weight((n, coordinator)))
    return g


def invert_weights(g):
    """
    Invert the weights of the given graph.

    The most expensive links will then be the cheapest and vice versa.
    """

    assert isinstance(g, digraph)

    # Determine the most expensive edge
    w = 0
    for (s,d) in g.edges():
        w = max(w, g.edge_weight((s,d)))
    print 'Maximum edge weight is %d' % w
    w += 1 # Make sure the most expensive edge will have a cost of 1 afterwards
    g_inv = digraph()
    for n in g.nodes():
        g_inv.add_node(n)
    for (s,d) in g.edges():
        assert g.edge_weight((s,d))<w
        w_inv = w-g.edge_weight((s,d))
        assert w_inv>0
        try:
            g_inv.add_edge((s,d), w_inv)
        except:
            assert g_inv.edge_weight((s,d)) == w_inv # This one fails
            print "Edge %d %d already in graph, ignoring .. " % (s,d)
    return g_inv


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
            logging.info("merge_graphs: adding edge %d %d failed" % (e[0], e[1]))
    for e in g2.edges():
        try:
            g.add_edge(e, g2.edge_weight(e))
        except:
            logging.info("merge_graphs: adding edge %d %d failed" % (e[0], e[1]))
    return g


def connect_graphs(g1, g2, connecting_edge, weight=1):
    """
    Build a new graph out of the two given graphs.

    Every node e in g1 will be represented as 1_e in the new graph and
    every node e' in g2 as 2_e'.

    @param connecting_edge: An edge (e_src, e_dst), where e_src is in
        g1 and e_dst is in g2. This edge will connect g1 with g2.
    @param weight: Weight of the connecting edge.
    """
    g = digraph()

    # Add nodes and edges
    for (index, gr) in [(1, g1), (2, g2)]:
        for n in gr.nodes():
            g.add_node('%d_%d' % (index, n))
        for (src, dst) in gr.edges():
            g.add_edge(('%d_%d' % (index, src),
                        '%d_%d' % (index, dst)),
                        g.edge_weight((src, dst)))

    # Connect subgraphs
    conn_src, conn_dst = connecting_edge
    g.add_edge(('%d_%d' % (1, conn_src),
                '%d_%d' % (2, conn_dst)))
    g.add_edge(('%d_%d' % (2, conn_dst),
                '%d_%d' % (1, conn_src)))

    return g


def F(n):
    if n == 0: return 0
    elif n == 1: return 1
    else: return F(n-1)+F(n-2)


def fibonacci(depth, nodes=[], edges=[], s=''):
    thisname = '%s%d' % (s, depth)

    num = 0

    # Append a node 0 only as right-hand child
    if depth<=0:
        return 0

    # End recursion and add one node
    elif depth==1:
        num += 1
        nodes.append(thisname)

    # Add node and recurse ..
    else:
        num += 1
        nodes.append(thisname)

        i = fibonacci(depth-1, nodes, edges, thisname, 'l')
        if i>0:
            edges.append((thisname, '%s%d' % (thisname, depth-1)))
            num += i

        i = fibonacci(depth-2, nodes, edges, thisname, 'r')
        if i>0:
            edges.append((thisname, '%s%d' % (thisname, depth-2)))
            num += 1

    return num
