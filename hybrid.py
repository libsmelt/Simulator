#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
from pygraph.classes.digraph import digraph

import overlay
import simplemachine
import helpers
from shm import ShmSpmc
import hybrid_model

class Hybrid(overlay.Overlay):
    """
    Generate a hybrid machine topology

    """
    
    def __init__(self, mod, mp_topology):
        """
        Initialize hybrid model

        @param mod The machine model
        @param mp_topology Topology class to use for global
        communication. This needs to be initialized somewhere.

        """
        super(Hybrid, self).__init__(mod)
        self.shm = []
        self.mp_topology = mp_topology

        self.do_shm = not self.mp_topology
        self.root = -1

        if self.do_shm:

            # There is no message passing tree
            self.mp_tree = None
            self.mp_tree_topo = None

            # choose first core to be sender - this ensures that the
            # sender's core ID is valid
            self.root = mod.get_cores()[0]
            self.shm.append(ShmSpmc(self.root,
                                    mod.get_cores(),
                                    None))

        elif self.mod.machine_topology:

            g = digraph()

            clusters = self.mod.machine_topology['Cache level 3']
            print str(clusters)
            coords = []

            for cluster in clusters.get():

                # First core in cluster acts as coordinator
                coords.append(cluster[0])

            print str(coords)
            coords = map(int, coords)
            g.add_nodes(coords)

            # Add all possible combinations of edges, with the weights
            # from the original model
            for c1 in coords:
                for c2 in coords:
                    if c1 != c2 and self.mod.get_graph().has_edge((c1, c2)):
                        g.add_edge((c1, c2), self.mod.get_graph().edge_weight((c1, c2)))

            self.mp_tree = self.mp_topology(simplemachine.SimpleMachine(g))
            tmp = self.mp_tree.get_broadcast_tree()
            print 'broadcast', str(tmp[0].graph)
            self.mp_tree_topo = tmp[0].graph

            for (cluster, coord) in zip(clusters.get(), coords):
                
                # Communication in clusters as shared memory
                # XXX Assume sequential send for cross-numa communication
                self.shm.append(ShmSpmc(coord, cluster, 
                                        self.mp_tree.get_root_node()))


            helpers.output_graph(self.mp_tree_topo, "hybrid_mp")

        else:
            # We don't currently support machines without coresenum
            # configuration. It should be easy to add, though. Just
            # run mp_topology on the entire graph. This essentially
            # corresponds to using a MP-only based implementation.

            raise Exception("Machine [%s] not in database, aborting!" % self.mod.name)

    def _get_broadcast_tree(self):
        """
        Generate a hybrid broadcast topology

        """
        if self.do_shm:
            return self.shm
        else:
            return self.shm + [ hybrid_model.MPTree(self.mp_tree_topo, self.mp_tree) ]
        
    def get_root_node(self):
        if self.do_shm:
            return self.root
        else:
            return self.mp_tree.get_root_node()

    def get_scheduler(self, graph):
        """
        XXX Graph is ignored!!
        """
        print "get_scheduler for hybrid tree using %s" % str(self.mp_tree)
        return self.mp_tree.get_scheduler(self.mp_tree._get_broadcast_tree())

    def get_name(self):
        
        return "Hybrid - " + self.mp_tree.get_name()
