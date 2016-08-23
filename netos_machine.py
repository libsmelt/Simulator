#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import sys

import model
import config

from pygraph.classes.digraph import digraph

# --------------------------------------------------
# NetOS base class
class NetosMachine(model.Model):
    """A machine model that parses the NetOS machine database for machines

    We intentionally did not use the NUMA model as a base class, which
    was meant as a dirty hack to auto-generate the graph for a
    machine. We can now (and should) do this directly from the
    pairwise measurements.

    Note: Currently this inherits from Model, but it should really
    not. The initialization here is completely separate from the base
    classes init code.


    We currently also parse hierarchical information from various
    Linux tools (lscpu, likwid). This is useful for hierarchical
    models (such as clusters), but also virtualization.

    """

    # Topology information as returned by the topology_parser
    res = None

    # Machine name
    name = None

    def __init__(self):
        """Initialize the Simulator for a NetOS machine.

        Read topology information from the NetOS machine DB and build
        a fully-connected graph representing the pairwise
        message-passing communication cost (as a sum of send and
        receive cost).

        """
        self.name = config.args.machine
        print 'Initializing NetOS machine %s' % self.name

        # Build a graph model
        super(NetosMachine, self).__init__()


    def get_name(self):
        return self.name


    def _build_graph(self):
        """Build a graph representing the communication cost within that
        machine.

        The cost of communication for each pair of cores is the
        send_cost + receive_cost on that link. This is set as edge
        weight and used by the schedulers when sorting
        edges.

        """

        _c_list = self.get_cores()

        # Add all cores to the graph
        gr = digraph()
        gr.add_nodes(_c_list)

        for snd in _c_list:
            for rcv in _c_list:
                if snd!=rcv:
                    snd_cost = self.get_send_cost(snd, rcv)
                    rcv_cost = self.get_receive_cost(snd, rcv)
                    gr.add_edge((snd, rcv), rcv_cost + snd_cost)

        return gr


    def __repr__(self):
        return self.name


# --------------------------------------------------
# Static function
def get_list():
    """Get list of NetOS machines
    """
    sys.path.append(config.MACHINE_DATABASE)
    from machineinfo import machines

    return [ s for (s, _, _) in machines ]
