#!/usr/bin/env python

import os
import sys

import model
import config
import topology_parser
import itertools

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
        
        self.res = topology_parser.parse_machine_db(self.name)
        print self.res
        
        # Parse pairwise send and receive costs. We need this to
        # build the graph with the pairwise measurements.
        super(NetosMachine, self)._parse_receive_result_file()
        super(NetosMachine, self)._parse_send_result_file()

        # Build a graph model
        super(NetosMachine, self).__init__(self._build_graph())
        

        
    def get_send_cost(self, src, dest):
        return super(NetosMachine, self)._get_send_cost(src, dest)

    def get_receive_cost(self, src, dest):
        return super(NetosMachine, self)._get_receive_cost(src, dest)

    
    def get_num_numa_nodes(self):
        """Get the number of NUMA nodes
        """
        return len(self.res['NUMA'].get())

    def get_cores_per_node(self):
        """Deprecated: This should ONLY be used for visualization purposes,
        and never for actually generating the model (use pairwise
        measurements for that)


        Assumptions: All NUMA nodes have the same number of cores.
        """
        return len(self.res['NUMA'].get()[0])

    def get_numa_information(self):
        return self.res['NUMA'].get()
    
    def get_num_cores(self):
        return self.res['numcpus']

    def get_name(self):
        return self.name

    def get_cores(self, only_active=False):
        c = list(itertools.chain.from_iterable(self.res['NUMA'].get()))
        c = self.filter_active_cores(c, only_active)
        return c
    
    def _build_graph(self):
        """Build a graph representing the communication cost within that
        machine.

        The cost of communication for each pair of cores is the
        send_cost + receive_cost on that link.

        """

        _c_list = self.get_cores()
        
        # Add all cores to the graph
        gr = digraph()
        gr.add_nodes(_c_list)
        
        for snd in _c_list:
            for rcv in _c_list:
                if snd!=rcv:
                    snd_cost = self._get_send_cost(snd, rcv)
                    rcv_cost = self._get_receive_cost(snd, rcv)
                    gr.add_edge((snd, rcv), snd_cost + rcv_cost)

        return gr


    def get_numa_id(self, core1):
        """Determine ID of the NUMA node <core1> resides on.
        """
        nodes = self.res['NUMA'].get()
        for (n, i) in zip(nodes, range(len(nodes))):
            if core1 in n:
                return i
            
    
        
# --------------------------------------------------
# Static function
def get_list():
    """Get list of NetOS machines
    """

    sys.path.append(config.MACHINE_DATABASE)
    from machineinfo import machines

    return [ s for (s, _, _) in machines ]


    
