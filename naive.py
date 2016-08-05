# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

# --------------------------------------------------
class Naive(scheduling.Scheduling):
    """
    Naive scheduling.

    Send messages in the order encoded in the model.
    """

    def find_schedule(self, sending_node, active_nodes=None):
        """
        Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @return List of neighbors in FIFO order.
        """
        return self._return_neighbors(sending_node, active_nodes)
