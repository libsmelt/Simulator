# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import model
import scheduling
import sort_longest
import sched_adaptive

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
            self.broadcast_tree = self._get_broadcast_tree()
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
        return sort_longest.SortLongest(final_graph)


