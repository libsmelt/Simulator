#!/usr/bin/env python

"""
The simulator consists of:
* machine model
* topology
* scheduler

"""

# Import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.algorithms.minmax import shortest_path

# Import own code
import evaluate
import config
import model
import helpers
import simulation

# Overlays
import overlay
import cluster
import ring
import binarytree
import sequential
import badtree
import mst
import adaptive
import hybrid

import scheduling
import ump

import pdb
import argparse
import logging
import sys
import os
import tempfile
import traceback
from config import topologies, machines

import numa_model

# Machines
import gruyere
import nos6
import ziger
import sbrinz
import gottardo
import appenzeller
import tomme
import rack

def arg_machine_class(string):
    """

    """
    if string == "gruyere":
        return gruyere.Gruyere
    elif string == "nos":
        return nos6.Nos
    elif string == 'ziger':
        return ziger.Ziger
    elif string == 'sbrinz':
        return sbrinz.Sbrinz
    elif string == 'gottardo':
        return gottardo.Gottardo
    elif string == 'appenzeller':
        return appenzeller.Appenzeller
    elif string == 'tomme':
        return tomme.Tomme
    else:
        if string in netos_machine.get_list():
            print "This is a Net OS machine"
            return netos_machine.NetosMachine
        else:
            raise Exception('Unknown machine %s' % string)
    

def arg_machine(machine_name):
    """
    Return instance of the machine given as argument

    """
    machine_name = config.translate_machine_name(machine_name)

    if machine_name == 'rack':
        return rack.Rack(sbrinz.Sbrinz)

    else:
        return arg_machine_class(machine_name)


# --------------------------------------------------
def build_and_simulate():
    """
    Build a tree model and simulate sending a message along it

    """
    # XXX The arguments are totally broken. Fix them!
    parser = argparse.ArgumentParser(
        description=('Simulator for multicore machines. The default action is '
                     'to simulate the given combination of topology and machine. '
                     'Available machines: %s' % ', '.join(config.machines) ))
    parser.add_argument('--evaluate-model', dest="action", action="store_const",
                        const="evaluate", default="simulate", 
                        help="Dump machine model instead of simulating")
    parser.add_argument('--evaluate-flounder', dest="action", action="store_const",
                        const="evaluate-flounder", default="simulate", 
                        help="?")
    parser.add_argument('--evaluate-ump', dest="action", action="store_const",
                        const="evaluate-ump", default="simulate", 
                        help="?")
    parser.add_argument('--evaluate-umpq', dest="action", action="store_const",
                        const="evaluate-umpq", default="simulate", 
                        help="?")
    parser.add_argument('--evaluate-all-machines', dest="action", 
                        action="store_const",
                        const="evaluate-all-machines", default="simulate", 
                        help="Generate a plot comparing all topologies on all machines")
    parser.add_argument('--ump-breakdown', dest="action", action="store_const",
                        const="ump-breakdown", default="simulate", 
                        help="Dump machine model instead of simulating")
    parser.add_argument('--multicast', action='store_const', default=False, 
                        const=True, help='Perfom multicast rather than broadcast')
    parser.add_argument('machine',
                        help="Machine to simulate")
    parser.add_argument('overlay', nargs='+',
                        help="Overlay to use for atomic broadcast")
    parser.add_argument('--group', default=None,
                        help=("Coma separated list of node IDs that should be "
                              "part of the multicast group"))
    parser.add_argument('--debug', action='store_const', default=False, const=True)

    try:
        config.args = parser.parse_args()
    except:
        exit(1)

    print "machine: %s, topology: %s" % (config.args.machine, config.args.overlay)

    m_class = arg_machine(config.args.machine)
    m = m_class()
    assert m != None
    gr = m.get_graph()

    if config.args.multicast:
        print "Building a multicast"

    # --------------------------------------------------
    # Switch main action
    # XXX Cleanup required
    if config.args.action == "simulate":
        # Generate model headers
        helpers.output_quroum_start(m, len(config.args.overlay))
        all_last_nodes = []
        model_descriptions = []
        num_models = 0
        # Generate representation of each topology
        for _overlay in config.args.overlay:

            # type(topology) = hybrid.Hybrid | binarytree.BinaryTree -- inherited from overlay.Overlay
            (topo, ev, root, sched, topology) = \
                simulation._simulation_wrapper(_overlay, m, gr, config.args.multicast)
            hierarchies = topo.get_tree()

            # Determine last node for this model
            d = helpers.core_index_dict(m.graph.nodes())
            all_last_nodes.append(d[m.evaluation.last_node])
            
            model_descriptions.append(topology.get_name())

            print "Cost for tree is: %d (%d), last node is %s" % (ev.time, ev.time_no_ab, ev.last_node)
            
            # Output c configuration for quorum program
            helpers.output_quorum_configuration( \
                        m, hierarchies, root, sched, topology, num_models)

            # Output final graph: we have to do this here, as the
            # final topology for the adaptive tree is not known before
            # simulating it.
            helpers.draw_final(m, sched)

            num_models += 1

        # Generate footer
        helpers.output_quorum_end(all_last_nodes, model_descriptions)
        return 0

    elif config.args.action == 'ump-breakdown':
        ump.execute_ump_breakdown()
        return 0

    elif config.args.action == "evaluate":
        print "Evaluating model"
        assert len(config.args.overlay) == 1 # Currently only supported if only one overlay is given
        helpers.parse_and_plot_measurement(
            range(m.get_num_cores()), config.args.machine, config.args.overlay[0], 
            config.get_ab_machine_results(config.args.machine, config.args.overlay))
        return 0

    elif config.args.action == "evaluate-ump":
        print "Evaluate UMP measurements for given machine"

        assert config.args.machine.startswith(m.get_name()) # E.g. ziger1 will be ziger, generally: machineNNN, where NNN is a number
        (results, sim_results) = helpers.extract_machine_results(m)

        # debug output
        for ((t, v, e), (t_sim, v_sim)) in zip(results, sim_results):
            print '%50s %7d %5d' % (t, v, v_sim)
            
        helpers.output_machine_results(
            config.translate_machine_name(config.args.machine), results, sim_results)

        return 0

    elif config.args.action == "evaluate-flounder":
        print "Evaluate FLOUNDER measurements for given machine"

        assert config.args.machine.startswith(m.get_name()) # E.g. ziger1 will be ziger, generally: machineNNN, where NNN is a number
        (results, sim_results) = helpers.extract_machine_results(m, nosim=True, flounder=True)

        # debug output
        for ((t, v, e), (t_sim, v_sim)) in zip(results, sim_results):
            print '%50s %7d %5d' % (t, v, v_sim)
            
        helpers.output_machine_results(
            config.translate_machine_name(config.args.machine), 
            results, sim_results, flounder=True)

        return 0

    elif config.args.action == "evaluate-umpq":
        print "Evaluate FLOUNDER measurements for given machine"

        assert config.args.machine.startswith(m.get_name()) # E.g. ziger1 will be ziger, generally: machineNNN, where NNN is a number
        (results, sim_results) = helpers.extract_machine_results(m, umpq=True)

        # debug output
        for ((t, v, e), (t_sim, v_sim)) in zip(results, sim_results):
            print '%50s %7d %5d' % (t, v, v_sim)
            
        # Tables
        helpers.output_machine_results(
            config.translate_machine_name(config.args.machine), 
            results, sim_results, umpq=True)

        # Plot
        helpers.plot_machine_results(
            config.translate_machine_name(config.args.machine),
            results, sim_results)
        
        return 0

    elif config.args.action == "evaluate-all-machines":
        print "Evaluate all machines"

        a = []

        for machine in machines:
            mod = arg_machine(machine) 
            (results, sim_results) = helpers.extract_machine_results(mod, nosim=True)

            a.append((machine, results))#, sim_results)
        
        fname = '/tmp/multiplot.tex'
        f = open(fname, 'w+')
        helpers._latex_header(f)

        # Generate plot including figure environment
        helpers.do_pgf_multi_plot(f, a)

        helpers._latex_footer(f)
        helpers.run_pdflatex(fname)

        return 0

    else:
        print 'Unknown action .. '
        exit(1)

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

    # --------------------------------------------------
    sched = topo.get_scheduler(final_graph)

    # --------------------------------------------------
    # Evaluate
    evaluation = evaluate.Evaluate()
    ev = evaluation.evaluate(topo, root, m, sched) 

    if config.args.debug:
        (fid, fname) = tempfile.mkstemp(suffix='.tex')
        f = open(fname, 'w+')
        helpers._latex_header(f)
        helpers._pgf_header(f)
        f.write('\\input{%s/%s}\n' % (os.getcwd(), ev.visu_name.replace('.tex','')))
        helpers._pgf_footer(f)
        helpers._latex_footer(f)
        f.close()

        helpers.run_pdflatex(fname)

if __name__ == "__main__":

    import netos_machine
    import config

    # Append NetOS machines
    config.machines += netos_machine.get_list()
    
    sys.excepthook = helpers.info
    build_and_simulate()
