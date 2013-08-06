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

        @param mp_topology: Topology class to use for global
        communication.

        """
        super(Hybrid, self).__init__(mod)
        self.shm = []
        self.mp_topology = mp_topology

        if self.mod.machine_topology:

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

            # Add all possible combinations of edges, with the weigts
            # from the original model
            for c1 in coords:
                for c2 in coords:
                    if c1 != c2 and self.mod.get_graph().has_edge((c1, c2)):
                        g.add_edge((c1, c2), self.mod.get_graph().edge_weight((c1, c2)))

            self.mp_tree = self.mp_topology(simplemachine.SimpleMachine(g))
            self.mp_tree_topo = self.mp_tree._get_broadcast_tree()

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

            raise Exception("Not supported!")

    def _get_broadcast_tree(self):
        """
        Generate a hybrid broadcast topology

        """
        
        return self.shm + [ hybrid_model.MPTree(self.mp_tree_topo) ]
        
    def get_root_node(self):
        return self.mp_tree.get_root_node()

    def get_scheduler(self, graph):
        """
        XXX Graph is ignored!!
        """
        print "get_scheduler for hybrid tree using %s" % str(self.mp_tree)
        return self.mp_tree.get_scheduler(self.mp_tree._get_broadcast_tree())