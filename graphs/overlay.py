# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import model

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

    def get_broadcast_tree(self):
        return None

    def get_coordinators(self):
        """
        Selects one coordinator per node for given model. 
        """
        coordinators=[]
        for core in range(len(mod.get_graph())):
            new_coordinator = True
            for c in coordinators:
                if mod.on_same_numa_node(core, c):
                    new_coordinator = False
            if new_coordinator:
                coordinators.append(core)
        print "Coordinator nodes are: %s" % str(coordinators)
        return coordinators



