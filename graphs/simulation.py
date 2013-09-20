# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Overlays
import cluster
import ring
import binarytree
import sequential
import badtree
import mst
import adaptive
import hybrid_model
import config

import helpers
import evaluate
import overlay

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

def _simulation_wrapper(ol, m, gr, multicast=False):
    """
    Wrapper for simulationg machines

    """
    print 'Simulating machine [%s] with topology [%s]' % \
        (m.get_name(), ol)

    r = overlay.Overlay.get_overlay(ol, m)

    root = r.get_root_node()

    if multicast:
        
        # Multicast, group membership given
        if config.args.group:
            n = config.args.group.split(',')

        # Multicast, group membership not given, use first half of nodes
        else:
            n = r.mod.get_graph().nodes()
            l = len(n)/2
            n = n[:l]

        print 'Multicast with nodes: %s' % ('-'.join(n))
        hybmod_list = r.get_multicast_tree(map(int, n))

    else:
        hybmod_list = r.get_broadcast_tree()

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

    assert isinstance(hybmod_list, list)

    # XXX Special treatment of non-hybird models
    if len(hybmod_list)==1 and isinstance(hybmod_list[0], hybrid_model.MPTree):
        final_graph = hybmod_list[0].graph
        sched = r.get_scheduler(final_graph)

        # --------------------------------------------------
        # Evaluate
        # XXX At this point we can only evaluate MP trees, 
        # so we search them in the hybrid model
        for l in hybmod_list:
            if isinstance(l, hybrid_model.MPTree):
                evaluation = evaluate.Evaluate()
                ev = evaluation.evaluate(r, root, m, sched) 

        # Return result
        return (r, ev, root, sched, r)

    else:
        raise Exception('XXX Don\' know how to get scheduler for list of modules')
