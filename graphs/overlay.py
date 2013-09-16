# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling
import sort_longest
import sched_adaptive
import config
import helpers

import random

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

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

    if overlay_name == "mst":
        r = mst.Mst

    elif overlay_name == "cluster":
        # XXX Rename to hierarchical 
        r = cluster.Cluster

    elif overlay_name == "ring":
        r = ring.Ring

    elif overlay_name == "bintree":
        r = binarytree.BinaryTree

    elif overlay_name == "sequential":
        r = sequential.Sequential

    elif overlay_name == "badtree":
        r = badtree.BadTree

    elif overlay_name == "adaptivetree":
        r = adaptive.AdapativeTree

    elif overlay_name == "fibonacci":
        r = fibonacci.Fibonacci

    else:
        raise Exception('Unknown topology')

    return r

def get_overlay(overlay_name, topo):
    import hybrid

    if overlay_name.startswith('hybrid_'):
        e = overlay_name.split('_')
        r_mp_class = get_overlay_class(e[1])
        r = hybrid.Hybrid(topo, r_mp_class)
    else:
        o = get_overlay_class(overlay_name)
        r = o(topo)
    return r

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
        return None

    def get_root_node(self):
        """
        Return root node. If model does not have any constraints, just
        start at 0

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
        assert not config.DO_MULTICAST

        if self.tree is None:
            tmp = self._get_broadcast_tree()
            helpers.output_graph(
                tmp,
                '%s_%s' % (self.mod.get_name(), self.get_name()),
                'dot')
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

