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
import itertools

import argparse
import logging
import sys
import os
import tempfile
import server
from config import machines



def simulate(args):

    machine = args.machine
    config.args.machine = args.machine
    config.args.group = args.group
    config.args.multicast = args.multicast
    config.args.multimessage = args.multimessage
    config.args.reverserecv = args.reverserecv
    config.args.hybrid = args.hybrid

    print "machine: %s, topology: %s, multimessage=%d, reverserecv=%d" % (machine, args.overlay, args.multimessage, args.reverserecv)

    m_class = config.arg_machine(machine)
    m = m_class(args.multimessage, args.reverserecv)
    assert m != None
    gr = m.get_graph()
    
    if args.multicast:
        print "Building a multicast"

    # --------------------------------------------------
    # Switch main action

    # XXX Cleanup required
    if True:

        # Generate model headers
        helpers.output_quroum_start(m, len(args.overlay))
        all_last_nodes = []
        all_leaf_nodes = []
        model_descriptions = []
        num_models = 0
        # Generate representation of each topology
        for _overlay in args.overlay:

            if config.args.multimessage :
                _overlay = _overlay + "-mm"
            if config.args.reverserecv :
                _overlay = _overlay + "-rev"  
            if config.args.hybrid :
                _overlay = _overlay + "-hybrid"
            # ------------------------------
            # Hybrid
            hyb_cluster = None
            shm_writers = None
            hyb_leaf_nodes = None

            if args.hybrid == 'True':

                if args.hybrid_cluster == "socket":
                    print "Clustering: Sockets"
                    hyb_cluster = m.machine_topology['Package'].get()

                else:
                    print "Clustering: NUMA nodes"
                    hyb_cluster = m.machine_topology['NUMA'].get()

                # Simulate a multicast tree
                args.multicast = True

                shm_writers = [ min(x) for x in hyb_cluster ]
                hyb_leaf_nodes = [ max(x) for x in hyb_cluster ]

                args.group = ','.join(map(str, shm_writers))


            # type(topology) = hybrid.Hybrid | binarytree.BinaryTree -- inherited from overlay.Overlay
            (topo, evs, root, sched, topology) = \
                simulation._simulation_wrapper(_overlay, m, gr, args.multicast)
            hierarchies = topo.get_tree()

            # Dictionary for translating core IDs
            d = helpers.core_index_dict(m.graph.nodes())

            tmp = topology.get_name()
            if hyb_cluster:
                tmp += " (hybrid)"
            model_descriptions.append(tmp)

            tmp_last_node = -1
            for (label, ev) in evs:
                if label == 'atomic broadcast':
                    tmp_last_node = ev.last_node
                print "Cost %s for tree is: %d (%d), last node is %s" % \
                    (label, ev.time, ev.time_no_ab, ev.last_node)

            # Output c configuration for quorum program
            helpers.output_quorum_configuration(m, hierarchies, root, sched,
                                                topology, num_models,
                                                shm_clusters=hyb_cluster,
                                                shm_writers=shm_writers)


            if args.hybrid == 'True':
                # Set ONE reader of the shared memory cluster as last node
                all_leaf_nodes.append(hyb_leaf_nodes)

                all_last_nodes.append(max(hyb_leaf_nodes))

            else:
                # Determine last node for this model
                all_leaf_nodes.append([d[l] for l in topo.get_leaf_nodes(sched)])

                # Determine last node for this model
                all_last_nodes.append(tmp_last_node)

                # Output final graph: we have to do this here, as the
                # final topology for the adaptive tree is not known before
                # simulating it.
                helpers.draw_final(m, sched, topo)

            num_models += 1


        # Generate footer
        helpers.output_quorum_end(all_last_nodes, all_leaf_nodes, \
                                  model_descriptions)
        return (all_last_nodes, all_leaf_nodes, root)

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
    parser.add_argument('machine', default=None, nargs='?',
                        help="Machine to simulate")
    parser.add_argument('overlay', nargs='*', default=config.topologies,
                        help="Overlay to use for atomic broadcast (default: %s)" %
                        ' '.join(config.topologies))
    parser.add_argument('--hybrid', action='store_const', default=False,
                        const=True, help='Generate hybrid model')
    parser.add_argument('--hybrid-cluster', help='how to cluster: default: numa, one of: numa, socket')
    parser.add_argument('--group', default=None,
                        help=("Coma separated list of node IDs that should be "
                              "part of the multicast group"))
    parser.add_argument('--visu', help='Visualize generated graph',
                        action='store_const', default=False, const=True)
    parser.add_argument('--debug',
                        action='store_const', default=False, const=True)
    parser.add_argument('--server', action='store_const', default=False, const=True)

    parser.add_argument('--multimessage', action='store_const', default=False, const=True)
    parser.add_argument('--reverserecv', action='store_const', default=False, const=True)

    try:
        config.args = parser.parse_args()
    except:
        exit(1)

    if config.args.debug:
        print 'Activating debug mode'
        import debug
        logging.getLogger().setLevel(logging.INFO)


    if config.args.server:
        from server import server_loop
        server_loop()


    if config.args.group:
        config.args.group = map(int, config.args.group.split(','))

    simulate(config.args)

    return 0


    # --------------------------------------------------
    # Output graphs
#    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

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
