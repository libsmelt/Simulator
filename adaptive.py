#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

from pygraph.classes.digraph import digraph

import sched_adaptive
import overlay
import logging

class AdapativeTree(overlay.Overlay):
    """
    Build a cluster topology for a model.

    """

    supported_args = [ "shuffle", "sort", "mm" ]

    def __init__(self, mod):
        """
        """
        super(AdapativeTree, self).__init__(mod)

    def get_name(self):
        name = "adaptivetree"
        for (key, value) in self.options.items() :
            if value :
                name = name + "-" + key

        return name

    def set_arguments(self, args):
        for a in args:
            if not a in self.supported_args:
                raise Exception(('Onrecognized argument %s' % a))
            else:
                self.options[a] = True
        super(AdapativeTree, self).set_arguments(args)

    def get_scheduler(self, final_graph):
        return sched_adaptive.SchedAdaptive(final_graph, self.mod, self)

    def get_root_node(self):

        _c_snd_cost = {}
        cores = self.mod.get_cores(True)
        for c in cores:
            _sum = 0
            for r in cores:
                if (r!=c):
                    _sum += self.mod.get_send_cost(c, r, False, False)
            _c_snd_cost[c] = _sum

            logging.info(('%d: sum of send %d' % (c, _sum)))

        c_snd_cost = sorted(_c_snd_cost.items(), key=lambda x: x[1])
        (root, cost) = c_snd_cost[0]

        print 'Choosing node %d as root with cost %d' % \
            (root, cost)

        return root

    def _build_tree(self, g):
        """
        Will return a empty broadcast tree that has to be build later
        on. The tree being returned will have add one node per core,
        but no edges.

        """
        gout = digraph()
        map(gout.add_node, [ n for n in g.nodes() ])
        return gout
