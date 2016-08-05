class HybridModule(object):
    """
    Represents a module that can be used for composing together
    distributed algorithms.

    """

    def __init__(self, parent):
        self.parent = parent

    def get_parent(self):
        return self.parent


class MPTree(HybridModule):

    def __init__(self, graph, mp_ol):
        """Represent a message passing module

        @param graph (digraph) The graph to be used

        @param mp_ol (overlay) The mp_ol network of the messge
        passing component

        """
        self.graph = graph
        self.mp_ol = mp_ol
