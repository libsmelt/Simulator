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
import gruyere
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

# --------------------------------------------------
def build_and_simulate():
    """
    Build a tree model and simulate sending a message along it
    """

    m = gruyere.Gruyere()
    gr = m.get_graph()

    root = 0
    if config.TOPO_TREE:
        final_graph = _run_mst(gr)

    elif config.TOPO_CLUSTER:
        clustering = cluster.Cluster(m)
        final_graph = clustering.get_broadcast_tree()

    elif config.TOPO_RING:
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
