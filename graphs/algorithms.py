# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
import Queue
import logging

import tools

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


def invert_weights(g):
    """
    Invert the weights of the given graph.

    The most expensive links will then be the cheapest and vice versa.
    """
    
    # Determine the most expensive edge
    w = 0
    for (s,d) in g.edges():
        w = max(w, g.edge_weight((s,d)))
    print 'Maximum edge weight is %d' % w
    w += 1 # Make sure the most expensive edge will have a cost of 1 afterwards
    g_inv = graph()
    for n in g.nodes():
        g_inv.add_node(n)
    for (s,d) in g.edges():
        assert g.edge_weight((s,d))<w
        w_inv = w-g.edge_weight((s,d))
        assert w_inv>0
        try:
            g_inv.add_edge((s,d), w_inv)
        except:
            assert g_inv.edge_weight((s,d)) == w_inv
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
            logging.info("merge_graphs: adding edge %d %d" % (e[0], e[1]))
    for e in g2.edges():
        try: 
            g.add_edge(e, g2.edge_weight(e))
        except:
            logging.info("merge_graphs: adding edge %d %d" % (e[0], e[1]))
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

def clustering():
    """
    """

    # Calculate average
    avg = 0.0
    num = 0

    # Get machine
    # import gottardo
    # g = gottardo.Gottardo()
    import ziger
    g = ziger.Ziger()

    # State
    clusters = []
    for x in range(g.get_num_cores()):
        clusters.append([x])

    num_clusters_last = g.get_num_cores()

    # Find and store link costs
    import Queue
    links = Queue.PriorityQueue()
    for x in range(g.get_num_cores()):
        for y in range(x):
            if x != y:
                print "%d -> %d has cost %f" % (x, y, g.get_receive_cost(x,y))
                cost = (g.get_receive_cost(x,y) + g.get_receive_cost(y,x))/2
                links.put((cost, (x,y)))

    # Cluster nodes
    while True:

        # Get from list
        try:
            (prio, (src, dest)) = links.get(block=False)
        except:
            print "no more links"
            break

        print "%d -> %d at %f" % (src, dest, prio)

        # Terminate once the link cost is higher than 1.4 of the average
        # if num>0 and prio>avg/num*1.1:
        #     break
                
        _put_same_cluster(clusters, src, dest)
        avg += prio
        num += 1

        if len(clusters)<num_clusters_last:
            # Calcualte the stderr on all clusters .. and pick min
            import tools
            cmax = max(map(lambda x: _evaluate_cluster_goodness(x, g.get_receive_cost), clusters))
            print "%d (maxstderr=%f) ----> %s" % (len(clusters), cmax, str(clusters))
            num_clusters_last = len(clusters)

    # Sort clusters
    for c in clusters:
        c = c.sort()

    print num
    print clusters


def _evaluate_cluster_goodness(x, f):

    # Build list of all pairwise links in the cluster
    c = []
    for s in x:
        for r in x:
            if s != r:
                c.append(f(s,r))

    if len(c)<1:
        return -1

    print "Statistics for %s is %s" % (str(x), str(tools.statistics(c)))
    return tools.statistics_cropped(c)[1]

def _put_same_cluster(cluster, src, dest):

    destcluster = None

    # Find dest's cluster
    for c in cluster:
        if dest in c:
            destcluster = c
            break

    assert destcluster

    # Don't do anything if nodes are _already_ in same cluster
    if src in destcluster:
        return
    cluster.remove(destcluster)

    # Find src's cluster .. 
    for c in cluster:
        if src in c:
            # .. and add nodes fro dest's cluster
            for d in destcluster:
                c.append(d)
            break


def F(n):
    if n == 0: return 0
    elif n == 1: return 1
    else: return F(n-1)+F(n-2)
            
        
def fibonacci(depth, nodes=[], edges=[], s='', side=None):
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
    
