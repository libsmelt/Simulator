#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

# Import graphviz
import sys
import os
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
sys.path.append('/home/skaestle/bin/')
sys.path.append(os.getenv('HOME') + '/bin/')
import gv
import Queue
import logging
import re

import config

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

from pygraph.readwrite.dot import write

# For printing clusters
import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

SHM_REGIONS_OFFSET=20
SHM_SLAVE_START=150
SHM_MASTER_START=SHM_SLAVE_START + SHM_REGIONS_OFFSET

def output_clustered_graph(graph, name, clustering):
    """Will ommit edge labels
    """

    # Create AGraph via networkx
    G = nx.DiGraph()
    G.add_nodes_from(graph.nodes())
    G.add_edges_from(graph.edges())

    A = to_agraph(G)

    tableau20 = [ '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78',
                  '#2ca02c', '#98df8a', '#d62728', '#ff9896',
                  '#9467bd', '#c5b0d5', '#8c564b', '#c49c94',
                  '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7',
                  '#bcbd22', '#dbdb8d', '#17becf', '#9edae5' ]
    clist = [ tableau20[i*2] for i in range(0, len(tableau20)/2)]

    i = 0
    for c in clustering:
        A.add_subgraph(c, name='cluster_%d' % i, color=clist[i % len(clist)])
        i += 1

    name = 'graphs/%s.png' % name
    A.write(name + '.dot')
    A.draw(name, prog="dot")


def output_graph(graph, name, algorithm='neato'):
    """
    Output the graph as png image and also as text file
    @param name Name of the file to write to

    """
    dot = write(graph, True)
    gvv = gv.readstring(dot)

    name = 'graphs/%s' % name

    with open('%s.dot'%name, 'w') as f:
        f.write(dot)

    gv.layout(gvv, algorithm)
    gv.render(gvv, 'png', ('%s.png' % name))

F_MODEL='model.h'
F_MODEL_DEFS='model_defs.h'

def output_quorum_configuration(model, hierarchies, root, sched, topo, midx,
                                shm_clusters=None, shm_writers=None):
    """
    Output a C array representing overlay and scheduling
    @param hierarchies: List of HybridModules, each of which is responsible for
          sending messages for a group/cluster of cores
    @param topology: instanceof(overlay.Overlay)
    @param midx: index of the model currently generated
    @param shm_clusters: list(list(int)) Shared memory clusters to be added to the model
    @param shm_writers: list(int) Writers, one of each list
    """
    from overlay import Overlay
    from model import Model
    assert isinstance(model, Model)
    assert isinstance(topo, Overlay)

    import shm

    d = core_index_dict(model.graph.nodes())

    dim = model.get_num_cores()
    mat = [[0 for x in xrange(dim)] for x in xrange(dim)]

    import hybrid_model

    # Build the matrix
    for h in hierarchies:
        assert isinstance(h, hybrid_model.HybridModule)
        if isinstance(h, hybrid_model.MPTree):
            assert sched is not None
            walk_graph(h.graph, root, fill_matrix, mat, sched, d)
        elif isinstance(h, shm.ShmSpmc):
            send_shm(h, mat, d)
        else:
            import pdb; pdb.set_trace()
            raise Exception('Unsupported Hybrid Module')

    #  Add clusters
    if shm_clusters:

        cidx = 0
        for cluster in shm_clusters:

            # Find writer
            writer = [ c for c in cluster if c in shm_writers ]
            assert len(writer) == 1 # each cluster has exactly one writer
            writer = writer[0]

            readers = [ c for c in cluster if c not in shm_writers ]

            for reader in readers:
                mat[writer][reader] = cidx + SHM_MASTER_START
                mat[reader][writer] = cidx + SHM_SLAVE_START

            cidx += 1

            if cidx == SHM_REGIONS_OFFSET:
                raise Exception('Too many shared memory regions')


    # Generate c code
    stream = open(F_MODEL, "a")
    __matrix_to_c(stream, mat, midx)

    # Add this model to the list of models in config
    config.models.append(mat)


def output_quroum_start(model, num_models):
    """Output the header of the model files

    @param model: see output_quorum_configuration
    """

    stream = open(F_MODEL, "w")
    defstream = open(F_MODEL_DEFS, "w")
    __c_header_model_defs(defstream,
                          str(model),
                          model.get_num_cores())
    __c_header_model(stream)

    defstream.write('#define NUM_TOPOS %d\n' % num_models)

    config.models = []


def output_quorum_end(all_last_nodes, all_leaf_nodes, model_descriptions):
    """Output the footer of the model files

    @param all_last_nodes: list(int) - A list of last nodes as determined
    by the Simulator for each model.

    @param all_leaf_nodes: list(list(int)) - A list of leaf nodes for
    each model. These nodes do not have any children in the broadcast
    tree.

    @param model_description A string representation for each model

    """
    stream = open(F_MODEL, "a")
    defstream = open(F_MODEL_DEFS, "a")

    stream.write('int *_topo_combined[NUM_TOPOS] = {%s};\n' % \
                 ', '.join(['(int*) topo%i' % i for i in range(len(model_descriptions))]))
    stream.write('int **topo_combined = (int**) _topo_combined;\n');
    stream.write('char* _topo_names[NUM_TOPOS] = {%s};\n' % \
                 ', '.join(['"%s"' % s for s in model_descriptions]))
    stream.write('char **topo_names = (char**) _topo_names;\n')

    # Leaf nodes
    for (leaf_nodes, i) in zip(all_leaf_nodes, range(len(all_leaf_nodes))):
        stream.write((('std::vector<int> leaf_nodes%d {' % i) + \
                      ','.join(map(str, leaf_nodes)) + '};\n'));

    stream.write('std::vector<int> *_all_leaf_nodes[NUM_TOPOS] = {' + \
                 ','.join([ ('&leaf_nodes%d' % i) \
                            for i in range(len(all_leaf_nodes)) ]) + \
                 '};\n');
    stream.write('std::vector<int> **all_leaf_nodes = _all_leaf_nodes;\n')
    stream.write('std::vector<coreid_t> last_nodes = {' + \
                 ', '.join([ str(i) for i in all_last_nodes]) + \
                 '};\n')

    __c_footer(stream)
    __c_footer(defstream)


SEND_SHM_IDX=SHM_SLAVE_START
def send_shm(module, mat, core_dict):
    import shm

    global SEND_SHM_IDX
    assert isinstance(module, shm.ShmSpmc)
    assert module.sender in module.receivers
    d = { (recv, module.sender): SEND_SHM_IDX for recv in module.receivers}
    d[(module.sender, module.sender)] += SHM_REGIONS_OFFSET
    # Sender
    for r in module.receivers:
        mat[module.sender][r] = SEND_SHM_IDX + SHM_REGIONS_OFFSET
        if r != module.sender:
            mat[r][module.sender] = SEND_SHM_IDX
    SEND_SHM_IDX += 1
    assert SEND_SHM_IDX<(SHM_SLAVE_START+SHM_REGIONS_OFFSET)


def walk_graph(g, root, func, mat, sched, core_dict):
    """
    Function to walk the tree starting from root

    active = reachable, but not yet dealt with. Elements are tuples (node, parent)
    done = reachable and also handled

    """
    assert isinstance(g, graph) or isinstance(g, digraph)

    active = Queue.Queue()
    done = []

    active.put((root, None))

    while not active.empty():
        # get next
        (a, parent) = active.get()
        assert (not a in done)
        # remember that it was handled
        done.append(a)
        # mark the inactive neighbors as active
        nbs = []
        for nb in g.neighbors(a):
            if not nb in done:
                active.put((nb, a))
                nbs.append(nb)

        # call handler function
        func(a, nbs, parent, mat, sched, core_dict)


def draw_final(mod, sched, topo):
    """Draw a graph of the final schedule

    Draw clusters to visualize NUMA nodes.
    """

    import model
    import scheduling

    from overlay import Overlay
    assert isinstance(mod, model.Model)
    assert isinstance(sched, scheduling.Scheduling)
    assert isinstance(topo, Overlay)

    print 'Name of machine is:', mod.get_name()
    print 'Name of topology is:', topo.get_name()

    import pygraphviz as pgv
    A = pgv.AGraph()

    for c in mod.get_cores(True):
        leaf = c in topo.get_leaf_nodes(sched)
        if leaf:
            logging.info(('Drawing leaf %d' % c))
        A.add_node(c, color='grey' if leaf else 'black')

    for c in mod.get_cores(True):
        s =  sched.get_final_schedule(c)
        for ((_,r), i) in zip(s, range(len(s))):
            A.add_edge(c, r, label=str(i+1))

    mc = (len(mod.get_cores()) != len(mod.get_cores(True)))

    clist = [ 'red', 'green', 'blue', 'orange', 'grey', 'yellow', 'black', 'pink' ]

    draw_subgraph = not topo.get_name() in [ 'fibonacci', 'bintree' ]
    if draw_subgraph:
        i = 0
        for c in mod.get_numa_information():
            A.add_subgraph(c, name='cluster_%d' % i, color=clist[i % len(clist)])
            i += 1
    else:
        print 'Not drawing NUMA nodes'

    desc = 'mc' if mc else 'full'

    try:
        _name = 'graphs/final_%s-%s-%s.png' % (mod.get_name(), topo.get_name(), desc)
        A.draw(_name, prog='dot')
        A.draw('graphs/last.png', prog='dot')
        A.draw('graphs/last_%s.png' % mod.get_name(), prog='dot')
        A.write(_name + '.dot')

    except Exception as e:
        print 'Generating PNGs for graph topologies faield, continuing'
        print e


def fill_matrix(s, children, parent, mat, sched, core_dict):
    """
    @param s: Sending core
    @param children: Children of sending core
    @param parent: Parent node of sending core
    @param mat: Matrix to write at
    @param sched: Scheduler to use or None (in which case messages will be
          send to all nodes in children list in given order). If None,
          weights will be read from cost_dict
    @param core_dict: Dictionary for core name mapping

    """
    logging.info("%d -> %s"
                 % (core_dict[s], ','.join([ str(c) for c in children ])))
    i = 1

    # Build list of nodes to send the message to
    target_nodes = sched.get_final_schedule(s)

    # Send message
    for (_, r) in target_nodes:
        logging.info("%d -> %d [%r]" %
                     (core_dict[s], core_dict[r], r in children))
        if r in children:
            mat[core_dict[s]][core_dict[r]] = i
            i += 1

    if not parent == None:
        assert len(children)<90 # ?
        mat[core_dict[s]][core_dict[parent]] = 99


def __matrix_to_c(stream, mat, midx):
    """
    Print given matrix as C
    """
    dim = len(mat)
    stream.write("int topo%d[TOPO_NUM_CORES][TOPO_NUM_CORES] = {\n" % midx)
    # x-axis labens
    stream.write(("//   %s\n" % ' '.join([ "%2d" % x for x in range(dim) ])))
    for x in range(dim):
        stream.write("    {")
        for y in range(dim):
            stream.write("%2d" % mat[x][y])
            if y+1 != dim:
                stream.write(",")
        stream.write("}")
        stream.write(',' if x+1 != dim else ' ')
        stream.write((" // %2d" % x))
        stream.write("\n")
    stream.write("};\n\n")


def __c_header(stream, name):
    stream.write('#ifndef %s\n' % name)
    stream.write('#define %s 1\n\n' % name)

def __c_header_model_defs(stream, machine, dim):
    __c_header(stream, 'MULTICORE_MODEL_DEFS')
    stream.write('#define MACHINE "%s"\n' % machine)
    stream.write("#define TOPO_NUM_CORES %d\n\n" % dim)
    stream.write('#define TOPOLOGY "multi-model"\n')

    stream.write('#define SHM_SLAVE_START %d\n' % SHM_SLAVE_START)
    stream.write('#define SHM_SLAVE_MAX %d\n' %
                 (SHM_SLAVE_START + SHM_REGIONS_OFFSET - 1))
    stream.write('#define SHM_MASTER_START %d\n' %
                 (SHM_MASTER_START));
    stream.write('#define SHM_MASTER_MAX %d\n' %
                 (SHM_MASTER_START + SHM_REGIONS_OFFSET - 1));

def __c_header_model(stream):
    __c_header(stream, 'MULTICORE_MODEL')
    stream.write('#include "model_defs.h"\n\n')
    stream.write('#include <vector>\n\n')

def __c_footer(stream):
    stream.write("#endif\n")



# http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)


# http://stackoverflow.com/questions/12217537/can-i-force-debugging-python-on-assertionerror
def info(type, value, tb):
   if hasattr(sys, 'ps1') or not sys.stderr.isatty() or type != AssertionError:
      # we are in interactive mode or we don't have a tty-like
      # device, so we call the default hook
      sys.__excepthook__(type, value, tb)
   else:
      import traceback, pdb
      # we are NOT in interactive mode, print the exception...
      traceback.print_exception(type, value, tb)
      print
      # ...then start the debugger in post-mortem mode.
      pdb.pm()

def core_index_dict(n):
    """
    Return a dictionary with indices for cores

    """

    if isinstance(n[0], int):
        return {i: i for i in n}

    n = natural_sort(n)
    return { node: idx for (idx, node) in zip(range(len(n)), n)}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def warn(msg):
    print bcolors.WARNING + 'WARNING: ' + msg + bcolors.ENDC


def git_version():
    """Determine and return the GIT version

    """
    from subprocess import Popen, PIPE
    gitproc = Popen(['git', 'rev-parse','HEAD'], stdout = PIPE)
    (stdout, _) = gitproc.communicate()
    return stdout.strip()
