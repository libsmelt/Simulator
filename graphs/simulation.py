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
import overlay

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

def _simulation_wrapper(ol, m, gr):
    """
    Wrapper for simulationg machines

    """
    print 'Simulating machine [%s] with topology [%s]' % \
        (m.get_name(), ol)

    r = overlay.get_overlay(ol, m)

    root = r.get_root_node()
    final_graph = r.get_broadcast_tree()

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

    # --------------------------------------------------
    sched = r.get_scheduler(final_graph)

    # DEPRECATED: Old way of dealing with output graphs
    if isinstance(final_graph, graph) or isinstance(final_graph, digraph):
        helpers.output_graph(final_graph, '%s_%s' % (m.get_name(), ol))

        # --------------------------------------------------
        # Evaluate
        evaluation = evaluate.Evaluate()
        ev = evaluation.evaluate(r, root, m, sched) 

        # Return result
        return (r, ev, root, sched, r)

    else:
        ev = evaluate.Result(0, 0, 'n.a.')
        m.set_evaluation_result(ev)
        return (r, ev, root, sched, r)
