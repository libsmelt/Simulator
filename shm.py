#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
from hybrid_model import HybridModule
import overlay

class ShmSpmc(HybridModule):
    """
    """

    def __init__(self, sender, receivers, parent):
        super(ShmSpmc, self).__init__(parent)
        self.sender = sender
        self.receivers = receivers

class Shm(overlay.Overlay):
    """Dummy class for shared memory overlays

    """

    def get_name(self):
        return "Shared Memory"
