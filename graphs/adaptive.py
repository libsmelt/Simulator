# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

from pygraph.classes.graph import graph

import sched_adaptive
import overlay

class AdapativeTree(overlay.Overlay):
    """
    Build a cluster topology for a model.

    """
    
    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        XXX Do we actually need this?

        """
        super(AdapativeTree, self).__init__(mod)
        
    def get_name(self):
        return "adaptivetree"

    def get_scheduler(self, final_graph):
        return sched_adaptive.SchedAdaptive(final_graph, self.mod)

    def _get_broadcast_tree(self):
        """
        Will return a empty broadcast tree that has to be build later
        on. The tree being returned will have add one node per core,
        but no edges.

        """
        g = graph()
        for c in range(self.mod.get_num_cores()):
            g.add_node(c)
        return g
