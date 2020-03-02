#!/usr/bin/env python3
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

"""
The simulator consists of:
* machine model
* topology
* scheduler

"""

import config
import helpers
import simulation

import argparse
import logging
import sys

import sys
sys.path.append('./contrib/python-graph/core')


def simulate(args):

    machine = args.machine
    config.args.machine = args.machine
    config.args.group = args.group
    config.args.multicast = args.multicast
    config.args.hybrid = args.hybrid
    config.args.hybrid_cluster = args.hybrid_cluster

    print ("machine: %s, topology: %s, hybrid: %s" % \
            (machine, args.overlay, args.hybrid))

    m_class = config.arg_machine(machine)
    m = m_class()
    assert m != None
    gr = m.get_graph()

    if args.multicast:
        print ("Building a multicast")
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

            if config.args.hybrid :
                _overlay = _overlay + "-hybrid"

            # ------------------------------
            # Hybrid
            hyb_cluster = None
            shm_writers = None

            hyb_leaf_nodes = None

            if config.args.hybrid:

                print (args.hybrid_cluster)
                if 'socket' in args.hybrid_cluster:
                    print ("Clustering: Sockets")
                    hyb_cluster = m.machine_topology['Package'].get()
                elif 'all' in args.hybrid_cluster:
                    print ("Clustering: All cores")
                    hyb_cluster = [range(0, m.machine_topology['numcpus'])]
                elif 'numa' in args.hybrid_cluster:
                    print ("Clustering: NUMA nodes")
                    if len(args.hybrid_cluster) > 4:
                        hyb_cluster = m.machine_topology['NUMA'].get()
                        size = float(args.hybrid_cluster[4:])

                        if size > 1:
                            # Merge NUMA nodes
                            if ((size % 2) != 0):
                                raise Exception(('Only support powers of two for'
                                                 ' numa node merge'))
                            if (size > (len(hyb_cluster)/2)):
                                raise Exception(('Only support values less or equal to half'
                                                 'the numa nodes'))
                            new_cluster = []
                            for i in range(0,len(hyb_cluster), int(size)):
                                tmp = []
                                for j in range(0, int(size)):
                                    tmp += hyb_cluster[i+j]

                                new_cluster.append(tmp)
                            hyb_cluster = new_cluster
                        else:
                            # Split NUMA nodes
                            print (hyb_cluster)
                            new_cluster = []
                            split = int(1/size)
                            if split > (len(hyb_cluster[0])/2):
                                raise Exception(('Single core in clusters not allowed'))
                            if (len(hyb_cluster[0]) % split) != 0:
                                raise Exception(('Only support splitting numa nodes if'
                                                 ' the numa size is divisible by the number'
                                                 ' of splits'))
                            for i in range(0, len(hyb_cluster)):
                                seg_len = int(len(hyb_cluster[0])/split)
                                for j in range(1, split+1):
                                    tmp1 = hyb_cluster[i][(j-1)*seg_len:j*seg_len]
                                    new_cluster.append(tmp1)

                            hyb_cluster = new_cluster
                            print (hyb_cluster)
                    else:
                        hyb_cluster = m.machine_topology['NUMA'].get()
                else:
                    print ("Warning: Unknown cluster argument for hybrid, using default option")
                    print ("Clustering: NUMA nodes")
                    hyb_cluster = m.machine_topology['NUMA'].get()

                # Simulate a multicast tree
                args.multicast = True

                shm_writers = [ min(x) for x in hyb_cluster ]
                hyb_leaf_nodes = [ max(x) for x in hyb_cluster ]

                args.group = map(int, shm_writers)
                config.args.group = map(int, shm_writers)
                #args.group = ','.join(map(str, shm_writers))

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
            receive_order = None
            for (label, ev) in evs:
                if label == 'atomic broadcast':
                    tmp_last_node = ev.last_node
                    receive_order = ev.node_finished_list
                print ("Cost %s for tree is: %d (%d), last node is %s" % \
                                    (label, ev.time, ev.time_no_ab, ev.last_node))

            assert receive_order != None

            # Output c configuration for quorum program
            helpers.output_quorum_configuration(m, hierarchies, root, sched,
                                                topology, num_models,
                                                shm_clusters=hyb_cluster,
                                                shm_writers=shm_writers)


            if config.args.hybrid:
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
                if not config.running_as_server:
                    helpers.draw_final(m, sched, topo)

            num_models += 1

        print (all_leaf_nodes)

        # Cut down number of leafs
        LEAFS_MAX = 10
        if len(all_leaf_nodes[0])>LEAFS_MAX:
            # Filter last nodes, only taking leaf nodes
            _l = [ x for x in receive_order if x in all_leaf_nodes[0] ]
            assert(len(_l) >= len(all_leaf_nodes[0]))
            all_leaf_nodes[0] = _l[-10:]
            helpers.warn('Cropping leaf nodes to: %s' % ','.join(map(str, all_leaf_nodes[0])))

        helpers.warn('Leaf nodes are: %s - %d' % (','.join(map(str, all_leaf_nodes[0])), len(all_leaf_nodes[0])))


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

    try:
        config.args = parser.parse_args()
    except:
        exit(1)

    if config.args.debug:
        print ('Activating debug mode')
        #$import debug
        #asert type(debug.info)!=None
        logging.getLogger().setLevel(logging.INFO)


    if config.args.server:
        from server import server_loop
        server_loop()


    if config.args.group:
        config.args.group = map(int, config.args.group.split(','))

    if config.args.hybrid:
        config.args.hybrid = 'True'

    simulate(config.args)

    return 0


if __name__ == "__main__":

    import netos_machine
    print ('Starting Simulator v%s' % helpers.git_version())

    # Append NetOS machines
    config.machines += netos_machine.get_list()

    sys.excepthook = helpers.info
    build_and_simulate()
