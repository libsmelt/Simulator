#!/usr/bin/env python

# Import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.minmax import minimal_spanning_tree

# Import own code
import evaluate
import config
import model
import cluster
import ring
import helpers

import pdb

# --------------------------------------------------

CORES_PER_NODE = 4
NUM_NUMA_NODES = 8
NUM_CORES = (CORES_PER_NODE*NUM_NUMA_NODES)
HOPCOST = 10
NUMACOST = 1

# Wrapper function to add edges between two NUMA nodes. 
def add_numa(graph, node1, node2, cost):
    n1 = node1*CORES_PER_NODE
    n2 = node2*CORES_PER_NODE
    for c1 in range(CORES_PER_NODE):
        for c2 in range(CORES_PER_NODE):
            src = (n1+c1)
            dest = (n2+c2)
            if src < dest:
                print "Adding edge %d -> %d with weight %d" % \
                    (src, dest, cost)
                graph.add_edge((src, dest), cost)

def connect_numa_nodes(g, g_numa, src, ):
    # assuming that routing is taking the shortes path,
    # NOT true on e.g. SCC
    connect_numa_internal(g, src)
    cost = shortest_path(g_numa, src)[1] # don't really know what the first argument is ..
    print "connect numa nodes for %d: cost array size is: %d" % \
        (src, len(cost))
    for trg in range(len(cost)):
        if src!=trg:
            add_numa(g, src, trg, cost[trg]*HOPCOST)

# fully connect numa islands!
def connect_numa_internal(graph, numa_node):
    for i in range(CORES_PER_NODE):
        for j in range(CORES_PER_NODE):
            if j>i:
                node1 = numa_node*CORES_PER_NODE + i
                node2 = numa_node*CORES_PER_NODE + j
                graph.add_edge((node1, node2), NUMACOST)

# --------------------------------------------------
def build_and_simulate():
    """
    Build a tree model and simulate sending a message along it
    """

    # Graph creation
    gr = graph()
    g_numa = graph()

    dbg_num_edges = 0
    for n in range(NUM_CORES):
        dbg_num_edges += n

    print "Expecting %d edges" % dbg_num_edges

    # --------------------------------------------------
    # --- g_numa
    # Construct graph of NUMA nodes
    # This graph expresses the cost of sending messages between
    # NUMA nodes.

    g_numa.add_nodes(range(NUM_NUMA_NODES))

    for i in range(3):
        g_numa.add_edge((i, i+1)) # to right, top row
        g_numa.add_edge((i, i+4)) # top to bottom row

    for i in range(4,7):
        g_numa.add_edge((i, i+1)) # to right, bottom row

    # remainig edges
    g_numa.add_edge((2,7))
    g_numa.add_edge((3,6))
    g_numa.add_edge((3,7))

    helpers.output_graph(g_numa, 'g_numa_tmp')


    # --------------------------------------------------
    # --- gr
    # Build fully meshed machine graph
    gr.add_nodes(range(NUM_CORES))

    for n in range(NUM_NUMA_NODES):
        connect_numa_nodes(gr, g_numa, n)

    # Append second gruyere-like machine
    # gr.add_nodes(range(NUM_CORES,2*NUM_CORES))

    # for n in range(NUM_NUMA_NODES, 2*NUM_NUMA_NODES):
    #     connect_numa_nodes(gr, g_numa, n)


    root = 0
    if config.TOPO_TREE:
        final_graph = _run_mst(gr)

    elif config.TOPO_CLUSTER:
        m = model.Gruyere(gr)
        clustering = cluster.Cluster(m)
        final_graph = clustering.get_broadcast_tree()

    elif config.TOPO_RING:
        m = model.Gruyere(gr)
        r = ring.Ring(m)
        final_graph = r.get_broadcast_tree()
        root = 8

    # --------------------------------------------------
    # Output graphs

    # helpers.output_graph(gr, 'gruyere')
    # helpers.output_graph(g_numa, 'numa')
    # helpers.output_graph(final_graph, 'mst')

    # --------------------------------------------------
    print "Cost for tree is: %d" % evaluate.evalute(final_graph, root)

def _run_mst(gr):
    """
    Run MST algorithm
    """
    mst = graph()
    mst.add_nodes(range(NUM_CORES))

    mst_edges = minimal_spanning_tree(gr)
    for i in range(len(mst_edges)):
        if mst_edges[i] != None:
            mst.add_edge((mst_edges[i], i), \
                             gr.edge_weight((mst_edges[i], i)))
    return mst


if __name__ == "__main__":
    build_and_simulate()
