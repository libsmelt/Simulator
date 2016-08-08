#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
class HybridModule(object):
    """
    Represents a module that can be used for composing together
    distributed algorithms.

    """

    def __init__(self, parent):
        self.parent = parent

class MPTree(HybridModule):

    def __init__(self, graph, mp_ol):
        """Represent a message passing module

        @param graph (digraph) The graph to be used

        @param mp_ol (overlay) The mp_ol network of the messge
        passing component

        """
        self.graph = graph
        self.mp_ol = mp_ol
