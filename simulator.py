#!/usr/bin/env python

"""
The simulator consists of:
* machine model
* topology
* scheduler

"""

# Import own code
import evaluate
import config
import helpers
import simulation

import argparse
import logging
import sys
import os
import tempfile
from config import machines

# --------------------------------------------------
def build_and_simulate():
    """
    Build a tree model and simulate sending a message along it

    """
    # XXX The arguments are totally broken. Fix them!
    parser = argparse.ArgumentParser(
        description=('Simulator for multicore machines. The default action is '
                     'to simulate the given combination of topology and machine. '
                     'Available machines: %s' % ', '.join(config.machines) ))
    parser.add_argument('--multicast', action='store_const', default=False, 
                        const=True, help='Perfom multicast rather than broadcast')
    parser.add_argument('machine',
                        help="Machine to simulate")
    parser.add_argument('overlay', nargs='*', default=config.topologies,
                        help="Overlay to use for atomic broadcast (default: %s)" %
                        ' '.join(config.topologies))
    parser.add_argument('--hybrid', action='store_const', default=False,
                        const=True, help='Generate hybrid model')
    parser.add_argument('--group', default=None,
                        help=("Coma separated list of node IDs that should be "
                              "part of the multicast group"))
    parser.add_argument('--debug', action='store_const', default=False, const=True)

    try:
        config.args = parser.parse_args()
    except:
        exit(1)

    if config.args.debug:
        print 'Activating debug mode'
        import debug
        logging.getLogger().setLevel(logging.INFO)
        
    print "machine: %s, topology: %s" % (config.args.machine, config.args.overlay)

    m_class = config.arg_machine(config.args.machine)
    m = m_class()
    assert m != None
    gr = m.get_graph()

    if config.args.multicast:
        print "Building a multicast"

    # --------------------------------------------------
    # Switch main action
    
    # XXX Cleanup required
    if True:
        
        # Generate model headers
        helpers.output_quroum_start(m, len(config.args.overlay))
        all_last_nodes = []
        all_leaf_nodes = []
        model_descriptions = []
        num_models = 0
        # Generate representation of each topology
        for _overlay in config.args.overlay:


            # ------------------------------
            # Hybrid
            numa_nodes = None
            shm_writers = None
            
            if config.args.hybrid:

                # Simulate a multicast tree
                config.args.multicast = True

                numa_nodes = m.res['NUMA'].get()
                shm_writers = [ min(x) for x in numa_nodes ]

                config.args.group = ','.join(map(str, shm_writers))

                
            # type(topology) = hybrid.Hybrid | binarytree.BinaryTree -- inherited from overlay.Overlay
            (topo, evs, root, sched, topology) = \
                simulation._simulation_wrapper(_overlay, m, gr, config.args.multicast)
            hierarchies = topo.get_tree()

            # Dictionary for translating core IDs
            d = helpers.core_index_dict(m.graph.nodes())
            
            # Determine last node for this model
            all_last_nodes.append(d[m.evaluation.last_node])
            
            model_descriptions.append(topology.get_name())

            for (label, ev) in evs:
                print "Cost %s for tree is: %d (%d), last node is %s" % \
                    (label, ev.time, ev.time_no_ab, ev.last_node)
            
            # Output c configuration for quorum program
            helpers.output_quorum_configuration(m, hierarchies, root, sched,
                                                topology, num_models,
                                                shm_clusters=numa_nodes,
                                                shm_writers=shm_writers)

            # Output final graph: we have to do this here, as the
            # final topology for the adaptive tree is not known before
            # simulating it.
            helpers.draw_final(m, sched, topo)

            # Determine last node for this model
            all_leaf_nodes.append([d[l] for l in topo.get_leaf_nodes(sched)])
            
            num_models += 1

            
        # Generate footer
        helpers.output_quorum_end(all_last_nodes, all_leaf_nodes, \
                                  model_descriptions)
        return 0
    

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

    # --------------------------------------------------
    sched = topo.get_scheduler(final_graph)

    # --------------------------------------------------
    # Evaluate
    evaluation = evaluate.Evaluate()
    ev = evaluation.evaluate(topo, root, m, sched) 

    if config.args.debug:
        (fid, fname) = tempfile.mkstemp(suffix='.tex')
        f = open(fname, 'w+')
        helpers._latex_header(f)
        helpers._pgf_header(f)
        f.write('\\input{%s/%s}\n' % (os.getcwd(), ev.visu_name.replace('.tex','')))
        helpers._pgf_footer(f)
        helpers._latex_footer(f)
        f.close()

        helpers.run_pdflatex(fname)

if __name__ == "__main__":

    import netos_machine

    # Append NetOS machines
    config.machines += netos_machine.get_list()
    
    sys.excepthook = helpers.info
    build_and_simulate()
