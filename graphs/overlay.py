# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import model
import scheduling
import sort_longest
import sched_adaptive
import hybrid_model

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

def get_overlay_class(overlay_name):
    """


    """

    import mst
    import cluster
    import ring 
    import binarytree
    import sequential
    import badtree
    import adaptive

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
        assert isinstance(mod, model.Model)
        self.mod = mod
        self.broadcast_tree = None

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
    
    def get_broadcast_tree(self):
        """
        Return broadcast tree
        
        Will call _get_broadcast_tree on first execution and store
        tree in broadcast_tree
        """
        if self.broadcast_tree is None:
            tmp = self._get_broadcast_tree()
            if isinstance(tmp, graph) or isinstance(tmp, digraph):
                self.broadcast_tree = [ hybrid_model.MPTree(tmp) ]
            elif isinstance(tmp, list):
                self.broadcast_tree = tmp
            else:
                import pdb; pdb.set_trace()
                raise Exception('Result of _get_broadcast_tree is of unsupported data type')

        assert not self.broadcast_tree is None
        return self.broadcast_tree

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

