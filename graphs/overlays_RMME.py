# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

class Overlay:
    """
    Base class for finding the right overlay topology for a model
    """
    def get_broadcast_tree(self):
        return None

