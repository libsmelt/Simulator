# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Overlays
import cluster
import ring
import binarytree
import sequential
import badtree
import mst
import adaptive

import helpers
import evaluate

def _simulation_wrapper(overlay, m, gr):
    """
    Wrapper for simulationg machines

    """
    print 'Simulating machine [%s] with topology [%s]' % \
        (m.get_name(), overlay)

    if overlay == "mst":
        r = mst.Mst(m)

    elif overlay == "cluster":
        # XXX Rename to hierarchical 
        r = cluster.Cluster(m)

    elif overlay == "ring":
        r = ring.Ring(m)

    elif overlay == "bintree":
        r = binarytree.BinaryTree(m)

    elif overlay == "sequential":
        r = sequential.Sequential(m)

    elif overlay == "badtree":
        r = badtree.BadTree(m)

    elif overlay == "adaptivetree":
        r = adaptive.AdapativeTree(m)

    root = r.get_root_node()
    final_graph = r.get_broadcast_tree()

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())
    if final_graph is not None:
        helpers.output_graph(final_graph, '%s_%s' % (m.get_name(), overlay))

    # --------------------------------------------------
    sched = r.get_scheduler(final_graph)

    # --------------------------------------------------
    # Evaluate
    evaluation = evaluate.Evaluate()
    ev = evaluation.evaluate(r, root, m, sched) 
    
    # Return result
    return (r, ev, root, sched, r)
