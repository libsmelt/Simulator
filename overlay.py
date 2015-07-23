# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling
import sort_longest
import sched_adaptive
import config
import helpers

import random

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

class Overlay(object):
    """
    Base class for finding the right overlay topology for a model

    """
    def __init__(self, mod):
        """
        Initialize the clustering algorithm

        """
        import model
        assert isinstance(mod, model.Model)
        self.mod = mod
        self.tree = None

    def _get_broadcast_tree(self):
        """
        Return the broadcast tree as a graph

        :returns graph: Broadcast tree as graph

        """
        return self._build_tree(self.mod.get_graph())

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
        tree in broadcast_tree
        """
        if self.tree is None:
            
            # Get tree
            tmp = self._get_broadcast_tree()

            # Debug output of tree
            fname = '%s_%s' % (self.mod.get_name(), self.get_name())
            helpers.output_graph(tmp, fname, 'dot')

            if isinstance(tmp, graph) or isinstance(tmp, digraph):
                import hybrid_model
                self.tree = [ hybrid_model.MPTree(tmp) ]
            elif isinstance(tmp, list):
                self.tree = tmp
            else:
                import pdb; pdb.set_trace()
                raise Exception('Result of _get_broadcast_tree is of unsupported data type')

        assert not self.tree is None
        return self.tree

    def get_random_multicast_tree(self):
        """
        Get a multicast tree for a random set of nodes for this machine.

        """
        assert config.MULTICAST_RATIO<1 and config.MULTICAST_RATIO>0

        nodes = [ n for n in self.mod.get_graph() \
                      if random.random()<config.MULTICAST_RATIO ]

        print 'Multicast: using nodes %s' % ','.join(map(str, nodes))

        import hybrid_model
        self.tree = self.get_multicast_tree(nodes)
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
            
        import hybrid_model

        self.tree = [ hybrid_model.MPTree(self._get_multicast_tree(mctree)) ]
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
        print "Coordinator nodes are: %s" % str(coordinators)
        return coordinators

    def get_scheduler(self, final_graph):
        """
        XXX Currently only one scheduler per model

        """
        print "Initializing scheduler in overlay: %s" % str(final_graph)
        return sort_longest.SortLongest(final_graph)

    @staticmethod
    def get_overlay_class(overlay_name):
        """
        Return subclass of overlay that matches the given name

        """

        import mst
        import cluster
        import ring 
        import binarytree
        import sequential
        import badtree
        import adaptive
        import fibonacci

        d = {
            'mst': mst.Mst,
            'cluster': cluster.Cluster,
            'ring': ring.Ring,
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
        import hybrid

        if overlay_name.startswith('hybrid_'):
            e = overlay_name.split('_')
            r_mp_class = Overlay.get_overlay_class(e[1])
            r = hybrid.Hybrid(topo, r_mp_class)
        else:
            o = Overlay.get_overlay_class(overlay_name)
            r = o(topo)
        return r

