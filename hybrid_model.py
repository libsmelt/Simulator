import helpers

from pygraph.classes.digraph import digraph

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
    
    def __init__(self, graph):
        self.graph = graph

