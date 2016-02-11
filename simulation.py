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
import hybrid
import config

import helpers
import evaluate
import overlay

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

def _simulation_wrapper(ol, m, gr, multicast=False):
    """
    Wrapper for simulationg machines

    @param ol - Topology to Simulate
    @param m  - machine to run on


    @return (r, evaluation, root, scheduler, instanceof(overlay))

    """
    print 'Simulating machine [%s] with topology [%s] - multicast %d' % \
        (m.get_name(), ol, multicast)

    r = overlay.Overlay.get_overlay(ol, m)

    root = r.get_root_node()

    if multicast:
        
        # Multicast, group membership given
        n = config.get_mc_group()

        assert 0 in map(int, n) # root is likely to be 0 - so it should be part of the tree

        print 'Multicast with nodes: %s' % ('-'.join(map(str,n)))
        hybmod_list = r.get_multicast_tree(map(int, n))

    else:
        print 'Getting broadcast tree for ', str(r)
        hybmod_list = r.get_broadcast_tree()

    # --------------------------------------------------
    # Output graphs
#    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

    assert isinstance(hybmod_list, list)

    r_tmp = None
    skip_mp = False

    # If this is a hybrid, consider only the MP part for evaluation
    if isinstance(r, hybrid.Hybrid):
        r_tmp = r
        r = r.mp_tree # Get the Overlay for the MP part of the evaluation
        if not r:
            skip_mp = True
        print 'MP topology is', str(r)

    if not skip_mp:

        # XXX Special treatment of non-hybird models
        mp_model = None
        for tmp_model in hybmod_list:
            if isinstance(tmp_model, hybrid_model.MPTree):

                assert not mp_model # Otherwise, we found to MP trees in
                                    # the hybrid model, which we don't
                                    # support ATM

                mp_model = tmp_model
                final_graph = mp_model.graph
                mp_ol = mp_model.mp_ol
                print 'Getting scheduler for topology', str(r), \
                    'graph is', str(final_graph), \
                    'overlay is', str(mp_ol)
                
                # XXX r here is a class, and not an instance of the class

                sched = r.get_scheduler(final_graph)

        if not mp_model:
            raise Exception('XXX Do not know how to get scheduler for list of modules')

        # Evaluate the MP part
        ev = evaluate.Evaluate.evaluate_all(r, root, m, sched)

        # Return result
        if r_tmp:
            r = r_tmp
        return (r, ev, root, sched, r)

    else:
        from evaluate import Result
        ev = Result(-1, m.get_cores()[-1], "SHM")
        ev.time = -1
        m.set_evaluation_result(ev)
        import shm
        return (r_tmp, ev, root, None, shm.Shm(m))
