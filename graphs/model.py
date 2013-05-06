# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import pdb

# --------------------------------------------------
class Model:

    def on_same_numa_node(self, core1, core2):
        """
        Base model does not have any NUMA nodes
        """
        return True

    def __init__(self, graph):
        """
        We initialize models with the graph
        """
        self.graph = graph
        
    def get_graph(self):
        return self.graph
        
# --------------------------------------------------
class Gruyere(Model):

    # Definition of NUMA topology
    numa = ( 
        (0,1,2,3,), 
        (4,5,6,7,), 
        (8,9,10,11,), 
        (12,13,14,15,), 
        (16,17,18,19,), 
        (20,21,22,23,), 
        (24,25,26,27,), 
        (28,29,30,31) 
        )
    
    def on_same_numa_node(self, core1, core2):
        """
        Return whether two nodes are in the same NUMA region
        """
        for node in self.numa:
            if core1 in node:
                return core2 in node
        pdb.set_trace()
        return None
        
