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
        raise Exception('Unknown machine')
    

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
        'to simulate the given combination of topology and machine'))
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
    parser.add_argument('overlay', 
                        help="Overlay to use for atomic broadcast")
    parser.add_argument('--debug', action='store_const', default=False, const=True)
    args = parser.parse_args()

    print "machine: %s, topology: %s" % (args.machine, args.overlay)

    m_class = arg_machine(args.machine)
    m = m_class()
    assert m != None
    gr = m.get_graph()
    

    if args.multicast:
        print "Building a multicast"
        config.DO_MULTICAST=True

    # --------------------------------------------------
    # Switch main action
    # XXX Cleanup required
    if args.action == "simulate":
        (topo, ev, root, sched, topology) = \
            simulation._simulation_wrapper(args.overlay, m, gr, args.multicast)
        hierarchies = topo.get_tree()
        print "Cost for tree is: %d, last node is %s" % (ev.time, ev.last_node)
        # Output c configuration for quorum program
        helpers.output_quorum_configuration(
            m, hierarchies, root, sched, topology)
        return 0

    elif args.action == 'ump-breakdown':
        ump.execute_ump_breakdown()
        return 0

    elif args.action == "evaluate":
        print "Evaluating model"
        helpers.parse_and_plot_measurement(
            range(m.get_num_cores()), args.machine, args.overlay, 
            config.get_ab_machine_results(args.machine, args.overlay))
        return 0

    elif args.action == "evaluate-ump":
        print "Evaluate UMP measurements for given machine"

        assert args.machine.startswith(m.get_name()) # E.g. ziger1 will be ziger, generally: machineNNN, where NNN is a number
        (results, sim_results) = helpers.extract_machine_results(m)

        # debug output
        for ((t, v, e), (t_sim, v_sim)) in zip(results, sim_results):
            print '%50s %7d %5d' % (t, v, v_sim)
            
        helpers.output_machine_results(
            config.translate_machine_name(args.machine), results, sim_results)

        return 0

    elif args.action == "evaluate-flounder":
        print "Evaluate FLOUNDER measurements for given machine"

        assert args.machine.startswith(m.get_name()) # E.g. ziger1 will be ziger, generally: machineNNN, where NNN is a number
        (results, sim_results) = helpers.extract_machine_results(m, nosim=True, flounder=True)

        # debug output
        for ((t, v, e), (t_sim, v_sim)) in zip(results, sim_results):
            print '%50s %7d %5d' % (t, v, v_sim)
            
        helpers.output_machine_results(
            config.translate_machine_name(args.machine), 
            results, sim_results, flounder=True)

        return 0

    elif args.action == "evaluate-umpq":
        print "Evaluate FLOUNDER measurements for given machine"

        assert args.machine.startswith(m.get_name()) # E.g. ziger1 will be ziger, generally: machineNNN, where NNN is a number
        (results, sim_results) = helpers.extract_machine_results(m, umpq=True)

        # debug output
        for ((t, v, e), (t_sim, v_sim)) in zip(results, sim_results):
            print '%50s %7d %5d' % (t, v, v_sim)
            
        # Tables
        helpers.output_machine_results(
            config.translate_machine_name(args.machine), 
            results, sim_results, umpq=True)

        # Plot
        helpers.plot_machine_results(
            config.translate_machine_name(args.machine),
            results, sim_results)
        
        return 0

    elif args.action == "evaluate-all-machines":
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

    # --------------------------------------------------
    # Output graphs
    helpers.output_graph(gr, '%s_full_mesh' % m.get_name())

    # --------------------------------------------------
    sched = topo.get_scheduler(final_graph)

    # --------------------------------------------------
    # Evaluate
    evaluation = evaluate.Evaluate()
    ev = evaluation.evaluate(topo, root, m, sched) 

    if args.debug:
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
    sys.excepthook = helpers.info
    try:
        build_and_simulate()
    except:
        print "Simulator terminated unexpectedly"
        print traceback.format_exc()
        sys.exit(1)
