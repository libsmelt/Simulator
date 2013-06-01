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
import helpers

# Machines
import gruyere
import nos6
import ziger
import sbrinz
import gottardo
import appenzeller

# Overlays
import cluster
import ring
import binarytree
import sequential
import badtree

import scheduling
import sort_longest

import pdb
import argparse
import logging
import sys
import os

def arg_machine(s):
    # Remove digits from machine name!
    string = ''.join([i for i in s if not i.isdigit()])
    if string == "gruyere":
        return gruyere.Gruyere()
    elif string == "nos":
        return nos6.Nos()
    elif string == 'ziger':
        return ziger.Ziger()
    elif string == 'sbrinz':
        return sbrinz.Sbrinz()
    elif string == 'gottardo':
        return gottardo.Gottardo()
    elif string == 'appenzeller':
        return appenzeller.Appenzeller()
    else:
        return None

# --------------------------------------------------
def build_and_simulate():
    """
    Build a tree model and simulate sending a message along it
    """
    topologies = [
        "ring", 
        "cluster", 
        "mst", 
        "bintree",
        "sequential",
        "badtree"
        ]
    machines = [
        "nos6",
        "ziger1",
        "gruyere",
        'sbrinz1', 'sbrinz2',
        'gottardo',
        'appenzeller'
        ]
    parser = argparse.ArgumentParser(
        description='Simulator for multicore machines')
    parser.add_argument('--evaluate-model', dest="action", action="store_const",
                        const="evaluate", default="simulate", 
                        help="Dump machine model instead of simulating")
    parser.add_argument('--evaluate-machine', dest="action", action="store_const",
                        const="evaluate-machine", default="simulate", 
                        help="Dump machine model instead of simulating")
    parser.add_argument('machine', choices=machines,
                        help="Machine to simulate")
    parser.add_argument('overlay', choices=topologies,
                        help="Overlay to use for atomic broadcast")
    args = parser.parse_args()

    m = arg_machine(args.machine)
    assert m != None
    gr = m.get_graph()
    
    # --------------------------------------------------
    # Switch main action
    # XXX Cleanup required
    if args.action == "simulate":
        (final_graph, ev, root, sched, topology) = _simulation_wrapper(args, m, gr)
        print "Cost for tree is: %d, last node is %d" % (ev.time, ev.last_node)
        # Output c configuration for quorum program
        helpers.output_quorum_configuration(m, final_graph, root, sched, topology)

    elif args.action == "evaluate":
        print "Evaluating model"
        helpers.parse_and_plot_measurement(
            range(m.get_num_cores()), args.machine, args.overlay, 
            ("%s/measurements/atomic_broadcast/%s_%s" % 
             (os.getenv("HOME"), args.machine, args.overlay)))
        return 0
    elif args.action == "evaluate-machine":
        print "Evaluate all measurements for given machine"
        results = []
        sim_results = []
        for t in topologies:
            f = ("%s/measurements/atomic_broadcast/%s_%s" % 
                 (os.getenv("HOME"), args.machine, t))
            if not os.path.isfile(f):
                print 'Did not find measurement %s' % f
                continue
            # Real hardware
            stat = helpers.parse_measurement(f, range(m.get_num_cores()))
            assert len(stat) == 1 # Only measurements for one core
            results.append((t, stat[0][1], stat[0][2]))
            # XXX Simulation
            (final_graph, ev, root, sched, topo) = _simulation_wrapper(args, m, gr)
            sim_results.append((t, ev.time))
        helpers.output_machine_results(args.machine, results, sim_results)
        return 0

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())
    helpers.output_graph(final_graph, '%s_%s' % (m.get_name(), args.overlay))

    # --------------------------------------------------
    # XXX Make this an argument
    sched = sort_longest.SortLongest(final_graph)

    # --------------------------------------------------
    # Evaluate
    ev = evaluate.evalute(final_graph, root, m, sched) 


def _simulation_wrapper(args, m, gr):
    root = 0
    if args.overlay == "mst":
        final_graph = _run_mst(gr, m)
        r = "mst"

    elif args.overlay == "cluster":
        # Rename to hierarchical 
        r = cluster.Cluster(m)
        final_graph = r.get_broadcast_tree()

    elif args.overlay == "ring":
        r = ring.Ring(m)
        final_graph = r.get_broadcast_tree()
        root = 8

    elif args.overlay == "bintree":
        r = binarytree.BinaryTree(m)
        final_graph = r.get_broadcast_tree()
        root = 0

    elif args.overlay == "sequential":
        r = sequential.Sequential(m)
        final_graph = r.get_broadcast_tree()
        root = 0

    elif args.overlay == "badtree":
        r = badtree.BadTree(m)
        final_graph = r.get_broadcast_tree()
        root = 0

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())
    helpers.output_graph(final_graph, '%s_%s' % (m.get_name(), args.overlay))

    # --------------------------------------------------
    # XXX Make this an argument
    sched = sort_longest.SortLongest(final_graph)

    # --------------------------------------------------
    # Evaluate
    ev = evaluate.evalute(final_graph, root, m, sched) 
    
    # Return result
    return (final_graph, ev, root, sched, r)


def _run_mst(gr, model):
    """
    Run MST algorithm
    XXX Move somewhere else
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
