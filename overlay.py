#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import scheduling
import helpers
import naive

import logging
import hybrid_model

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

class Overlay(object):
    """
    Base class for finding the right overlay topology for a model

    """

    """Broadcast tree - expressed as a hybrid model. List of hybrid_model.MPTree
    """
    tree = None

    def __init__(self, mod):
        """
        Initialize

        """
        import model
        assert isinstance(mod, model.Model)
        self.mod = mod
        self.tree = None
        self.options = {}

    def set_arguments(self, args):
        """Used to pass arguments to the overlay. Arguments are given like
        this: adaptivetree-optimized

        @param args list of strings
        """
        for a in args:
            print 'Overlay: activating argument: [%s]' % a
            self.options[a] = True
            # Some options have to be passed to the Machine
            if a == 'mm':
                self.mod.enable_mm = True


    def _get_broadcast_tree(self):

        """
        Return the broadcast tree as a graph

        :returns graph: Broadcast tree as graph

        """
        tmp = self._build_tree(self.mod.get_graph())
        assert isinstance(tmp, digraph)
        return tmp

    def _get_multicast_tree(self, g):
        """
        Return the multicast tree for the given subtree of the original model

        :param graph g: Input graph as subset of model to build the MC for
        :returns graph: Multicast tree as graph

        """
        return self._build_tree(g)

    def _build_tree(self, g):
        """
        Actual implementation of getting a {multi,broad}cast-tree.

        This includes the edge weight, which is the propagation time.
        :TODO: Make sure _build_tree returns a bigraph, also, make sure it has weights!

        :param graph g: A graph with group members as nodes and weighted edges expressing the cost of sending a message

        """
        raise Exception("Subclasses need to provide algorithm to build a tree")

    def get_root_node(self):
        """
        Return root node. If model does not have any constraints, just
        start at 0.

        """
        if self.mod.get_root_node():
            return self.mod.get_root_node()
        else:
            return 0

    def get_name(self):
        return None

    def get_tree(self):
        """
        Return previously generated tree. Functions generating a tree are:
        :py:func:`get_broadcast_tree`, :py:func:`get_random_multicast_tree`
        or :py:func:`get_multicast_tree`.

        :returns: Previously generated tree
        :rtype: List of :py:class:`hybrid_model.HybridModule`

        """
        return self.tree

    def get_broadcast_tree(self):
        """
        Return broadcast tree

        Will call _get_broadcast_tree on first execution and store
        tree in broadcast_tree.

        """
        if self.tree is None:

            print "Generating model"

            # Get tree
            tmp = self._get_broadcast_tree()

            # Debug output of tree
            fname = '%s_%s' % (self.mod.get_name(), self.get_name())
            helpers.output_clustered_graph(tmp, fname, self.mod.get_numa_information())

            if isinstance(tmp, graph) or isinstance(tmp, digraph):
                self.tree = [ hybrid_model.MPTree(tmp, self) ]

            elif isinstance(tmp, list):

                self.tree = tmp
            else:
                import pdb; pdb.set_trace()
                raise Exception('Result of _get_broadcast_tree is of unsupported data type')

        assert not self.tree is None
        return self.tree


    def get_multicast_tree(self, nodes):
        """
        Build a multicast tree for the given set of nodes

        """
        mctree = digraph()

        # Copy nodes
        for n in nodes:
            assert n in self.mod.get_graph().nodes()
            mctree.add_node(n)

        # Copy edges
        for (s,d) in self.mod.get_graph().edges():
            if s in nodes and d in nodes:
                mctree.add_edge((s,d), self.mod.get_graph().edge_weight((s,d)))

        self.tree = [ hybrid_model.MPTree(self._get_multicast_tree(mctree), self) ]
        return self.tree

    def get_coordinators(self):
        """
        Selects one coordinator per node for given model.
        """
        coordinators=[]
        for core in range(len(self.mod.get_graph())):
            new_coordinator = True
            for c in coordinators:
                if self.mod.on_same_numa_node(core, c):
                    new_coordinator = False
            if new_coordinator:
                coordinators.append(core)

        coordinators = self.mod.filter_active_cores(coordinators, True)
        print "Coordinator nodes are: %s" % str(coordinators)
        return coordinators

    def get_scheduler(self, final_graph):
        """Return a scheduler for the given topology and graph.
        """
        print "Initializing scheduler in overlay: %s" % str(final_graph)


        return naive.Naive(final_graph)


    @staticmethod
    def get_overlay_class(overlay_name):
        """
        Return subclass of overlay that matches the given name

        """

        import mst
        import cluster
        import binarytree
        import sequential
        import badtree
        import adaptive
        import fibonacci

        d = {
            'mst': mst.Mst,
            'cluster': cluster.Cluster,
            'bintree': binarytree.BinaryTree,
            'sequential': sequential.Sequential,
            'badtree': badtree.BadTree,
            'adaptivetree': adaptive.AdapativeTree,
            'fibonacci': fibonacci.Fibonacci
        }

        if overlay_name in d:
            r = d[overlay_name]

        else:
            supported = ', '.join([ x for (x, _) in d.items()])
            raise Exception('Unknown topology %s - Supported are: %s' % \
                            (overlay_name, supported))

        return r

    @staticmethod
    def get_overlay(overlay_name, topo):
        """
        @param topo That seems to be the machine!
        """
        import hybrid

        overlay = overlay_name.split('-')
        overlay_name = overlay[0]
        overlay_args = overlay[1:]

        if overlay_name == 'shm':
            r = hybrid.Hybrid(topo, None)
        elif overlay_name.startswith('hybrid_'):
            e = overlay_name.split('_')
            print 'Detected hybrid model with base class', e[1]
            r_mp_class = Overlay.get_overlay_class(e[1])
            assert len(overlay_args) == 0 # Don't know how to pass the
                                          # arguments for Hybrids
            r = hybrid.Hybrid(topo, r_mp_class)
        else:
            o = Overlay.get_overlay_class(overlay_name)
            r = o(topo)
            r.set_arguments(overlay_args)
        return r


    def get_leaf_nodes(self, sched):
        """Return leaf nodes in this topology

        @param sched scheduling.Scheduling The scheduler, which knows
        the final schedule. This is necessary as - for some reason -
        the tree stored with the overlay has edges in both directions
        for each connection in the broadcast tree.

        I think this is a bug, and once it is fixed, the Scheduler
        should really not be needed here.

        """

        assert isinstance(sched, scheduling.Scheduling)

        leaf_nodes = []

        for x in self.tree:
            if isinstance(x, hybrid_model.MPTree):

                logging.info(("Found message passing model", str(x.graph)))

                tree = x.graph

                for n in tree.nodes():

                    # OMG, edges are even dublicated in the Scheduler
                    # for some topologies!  How would I ever figure
                    # out which are the last nodes ..

                    # Currently working correctly are:
                    # - adaptive tree
                    # - binary tree
                    # - clustered
                    # - sequential
                    # - fibonacci
                    # - mst
                    # - badtree

                    l = [ y for (x,y) in tree.edges() if x == n ]

                    # For some Overlays, it seems that there are edges
                    # in the broadcast tree that are not atually used
                    # in the final Schedule. I saw this happening
                    # especially because for each edge (s, r), there
                    # is also (r, s) in the broadcast tree.
                    l_ = [ r for r in l if r in \
                           [ rr for (_, rr) in sched.get_final_schedule(n)] ]

                    if len(l) != len(l_):
                        helpers.warn('Overlay contains edged that are not in final schedule. This is a bug')

                    if len(l_)==0:
                        logging.info((n, 'is a leaf node'))
                        leaf_nodes.append(n)


        return leaf_nodes


    def get_parents(self, sched):
        """Return a dict with each cores parent node
        """

        assert isinstance(sched, scheduling.Scheduling)
        parents = {}

        for x in self.tree:
            if isinstance(x, hybrid_model.MPTree):

                logging.info(("Found message passing model", str(x.graph)))

                tree = x.graph

                for n in tree.nodes():

                    l = [ y for (x,y) in tree.edges() if x == n ]

                    # For some Overlays, it seems that there are edges
                    # in the broadcast tree that are not atually used
                    # in the final Schedule. I saw this happening
                    # especially because for each edge (s, r), there
                    # is also (r, s) in the broadcast tree.
                    l_ = [ r for r in l if r in \
                           [ rr for (_, rr) in sched.get_final_schedule(n)] ]

                    if len(l) != len(l_):
                        helpers.warn('Overlay contains edged that are not in final schedule. This is a bug')

                    logging.info(('Found children for', n, ' to ', str(l)))
                    for child in l:
                        parents[child] = n

        return parents
