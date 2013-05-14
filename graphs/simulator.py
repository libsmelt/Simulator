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
import nos6
import cluster
import ring
import helpers

import pdb
import argparse

def arg_machine(string):
    if string == "gruyere":
        return gruyere.Gruyere()
    elif string == "nos":
        return nos6.Nos()
    else:
        return None

# --------------------------------------------------
def build_and_simulate():
    """
    Build a tree model and simulate sending a message along it
    """
    parser = argparse.ArgumentParser(
        description='Simulator for multicore machines')
    parser.add_argument('machine', choices=['nos', 'gruyere'],
                        help="Machine to simulate")
    parser.add_argument('overlay', choices=["ring", "cluster", "tree"],
                        help="Overlay to use for atomic broadcast")
    args = parser.parse_args()

    m = arg_machine(args.machine)
    gr = m.get_graph()
    
    root = 0
    if args.overlay == "tree":
        final_graph = _run_mst(gr, m)

    elif args.overlay == "cluster":
        clustering = cluster.Cluster(m)
        final_graph = clustering.get_broadcast_tree()

    elif args.overlay == "ring":
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

def _run_mst(gr, model):
    """
    Run MST algorithm
    """
    mst = graph()
    mst.add_nodes(range(model.get_num_cores()))

    mst_edges = minimal_spanning_tree(gr)
    for i in range(len(mst_edges)):
        if mst_edges[i] != None:
            mst.add_edge((mst_edges[i], i), \
                             gr.edge_weight((mst_edges[i], i)))
    return mst


if __name__ == "__main__":
    build_and_simulate()
