#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

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
