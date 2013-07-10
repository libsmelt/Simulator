# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
import os
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv
import Queue
import numpy
import subprocess
import logging
import pdb
import traceback
import re
import simulation
from config import topologies, machines, get_ab_machine_results

from datetime import *

from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

from pygraph.readwrite.dot import write
from pygraph.algorithms.minmax import shortest_path

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


def output_quorum_configuration(model, graph, root, sched, topo):
    """
    Output a C array representing overlay and scheduling

    """
    d = core_index_dict(graph.nodes())
    
    dim = model.get_num_cores()
    mat = [[0 for x in xrange(dim)] for x in xrange(dim)]

    # Build the matrix
    walk_graph(graph, root, fill_matrix, mat, sched, d)

    # Determine longest path with most expensive node
    # ? < why is there a ?
    sp = shortest_path(graph, root)[1].items()
    sp.sort(key=lambda tup: tup[1], reverse=True)

    # Generate c code
    stream = open("model.h", "w")
    defstream = open("model_defs.h", "w")
    __c_header_model_defs(defstream, 
                          d[model.evaluation.last_node], 
                          type(model), 
                          type(topo),
                          len(mat))
    __c_header_model(stream)
    __matrix_to_c(stream, mat)
    __c_footer(stream)
    __c_footer(defstream)


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
        

def fill_matrix(s, children, parent, mat, sched, core_dict):
    """
    """
    logging.info("%d -> %s" 
                 % (core_dict[s], ','.join([ str(c) for c in children ])))
    i = 1
    for (cost, r) in sched.get_final_schedule(s):
        logging.info("%d -> %d [%r]" % 
                     (core_dict[s], core_dict[r], r in children))
        if r in children:
            mat[core_dict[s]][core_dict[r]] = i
            i += 1
    if not parent == None:
        assert len(children)<90
        mat[core_dict[s]][core_dict[parent]] = 99


def __matrix_to_c(stream, mat):
    """
    Print given matrix as C 
    """
    dim = len(mat)
    stream.write("int model[MODEL_NUM_CORES][MODEL_NUM_CORES] = {\n")
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

def __c_header_model_defs(stream, last_node, machine, topology, dim):
    __c_header(stream, 'MULTICORE_MODEL_DEFS')                               
    stream.write('#define MACHINE "%s"\n' % machine)
    stream.write('#define TOPOLOGY "%s"\n' % topology)
    stream.write('#define LAST_NODE %d\n' % last_node)
    stream.write("#define MODEL_NUM_CORES %d\n\n" % dim)

def __c_header_model(stream):
    __c_header(stream, 'MULTICORE_MODEL')                               
    stream.write('#include "model_defs.h"\n\n')

def __c_footer(stream):
    stream.write("#endif\n")


def clear_line(line):
    """
    Remove unneeded characters from given string
    """
    return line.rstrip('\r\n').replace('\t', '    ')

def _unpack_line_header(header):
    """
    Format: sk_m_print(<coreid>,<topology>)
    """
    start = "sk_m_print("
    assert header.startswith(start)
    assert header.endswith(")")
    result = str.split((header[len(start): len(header)-1]), ',')
    return (int(result[0]), result[1])


def unpack_line(line):
    """
    Unpacks a measurement line
    Format: sk_m_print(<coreid>,<topology>) idx= <index> tscdiff= <measurement>
    @return tuple (coreid, topology, index, measurement)
    """
    el = str.split(line)
    assert len(el) == 5
    return _unpack_line_header(el[0]) + (int(el[2]), int(el[4]))


def statistics_cropped(l, r=.1):
    """
    Print statistics for the given list of integers
    @param r Crop ratio. .1 corresponds to dropping the 10% highest values
    @return A tuple (mean, stderr, min, max)
    """
    if not isinstance(l, list) or len(l)<1:
        return None

    crop = int(len(l)*r)
    m = 0
    for i in range(crop):
        m = 0
        for e in l:
            m = max(m, e)
        l.remove(m)

    return statistics(l)


def statistics(l):
    """
    Print statistics for the given list of integers
    @return A tuple (mean, stderr, median, min, max)
    """
    if not isinstance(l, list) or len(l)<1:
        return None

    nums = numpy.array(l)

    m = nums.mean(axis=0)
    median = numpy.median(nums, axis=0)
    d = nums.std(axis=0)

    return (m, d, median, nums.min(), nums.max())


def _pgf_header(f, caption='TODO', label='TODO'):
    s = (("\\begin{figure}\n"
          "  \\caption{%s}\n"
          "  \\label{%s}\n"
          "  \\begin{tikzpicture}[scale=.75]\n") 
         % (caption, label))
    f.write(s)


def _pgf_plot_header(f, plotname, caption, xlabel, ylabel, attr=[], desc='...'):
    label = "pgfplot:%s" % plotname
    s = (("Figure~\\ref{%s} shows %s\n"
          "\\pgfplotsset{width=\linewidth}\n") % (label, desc))
    if xlabel:
        attr.append('xlabel={%s}' % xlabel)
    if ylabel:
        attr.append('ylabel={%s}' % ylabel)
    t = ("    \\begin{axis}[%s]\n") % (','.join(attr))
    f.write(s)
    _pgf_header(f, caption, label)
    f.write(t)


def _pgf_plot_footer(f):
    f.write("    \\end{axis}\n")
    _pgf_footer(f)


def _pgf_footer(f):
    s = ("  \\end{tikzpicture}\n"
         "\\end{figure}\n")
    f.write(s)

    
def do_pgf_plot(f, data, caption='', xlabel='', ylabel=''):
    """
    Generate PGF plot code for the given data
    @param f File to write the code to
    @param data Data points to print as list of tuples (x, y, err)
    """
    now = datetime.today()
    plotname = "%02d%02d%02d" % (now.year, now.month, now.day)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel)
    f.write(("    \\addplot[\n"
             "        color=red,\n"
             "        mark=x,\n"
             "        error bars/y dir=both,\n"
             "        error bars/y explicit\n"
             "        ] coordinates {\n"))

    for d in data:
        if d[2] < d[1]: # Drop data if error is too high
            f.write("      (%d,%f) +- (%f,%f)\n" % (d[0], d[1], d[2], d[2]))

    f.write("    };\n");
    _pgf_plot_footer(f)

def do_pgf_3d_plot(f, datafile, caption='', xlabel=None, ylabel=None, zlabel=None):
    """
    Generate PGF plot code for the given data
    @param f File to write the code to
    @param data Data points to print as list of tuples (x, y, err)
    """
    attr = ['scaled z ticks=false',
            'z tick label style={/pgf/number format/fixed}']
    if zlabel:
        attr.append('zlabel={%s}' % zlabel)
    now = datetime.today()
    plotname = "%02d%02d%02d" % (now.year, now.month, now.day)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel, attr)
    f.write(("    \\addplot3[surf] file {%s};\n") % datafile)
    _pgf_plot_footer(f)

def do_pgf_multi_plot(f, multidata, caption='FIXME', xlabel='FIXME', ylabel='FIXME'):
    """
    Same as do_pgf_multi_plot
    @param list of (label, [(x,y,err)])

    """
    now = datetime.today()
    plotname = "%02d%02d%02d" % (now.year, now.month, now.day)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel, 
                     attr=['ybar interval=.3'])

    machines = []
    topos = []
    data = []

    for (legentry, rawdata) in multidata:

        idata = []
        topos = []
        for d in rawdata:
            topos.append(d[0])
            idata.append(d[1])
 
        data.append(idata)

        machines.append(legentry)

    # "Invert" two dimensional list
    data_new = [[0 for i in range(len(data))] for j in range(len(data[0]))]
    for y in range(len(data[0])):
        for x in range(len(data)):
            tmp = data[x][y]
            data_new[y][x] = tmp

    for idata in data_new:
         f.write(("    \\addplot coordinates {\n"))
         i = 0
         for d in idata:
             f.write("      (%d,%f)\n" % (i, d))
             i += 1
         f.write("    };\n");

    f.write("\legend{%s}\n" % ','.join(topos))

    _pgf_plot_footer(f)
    


def _latex_header(f):
    header = (
        "\\documentclass[a4wide]{article}\n"
        "\\usepackage{url,color,xspace,verbatim,subfig,ctable,multirow,listings}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage{txfonts}\n"
        "\\usepackage{rotating}\n"
        "\\usepackage{paralist}\n"
        "\\usepackage{subfig}\n"
        "\\usepackage{graphics}\n"
        "\\usepackage{enumitem}\n"
        "\\usepackage{times}\n"
        "\\usepackage{amssymb}\n"
        "\\usepackage[colorlinks=true]{hyperref}\n"
        "\\usepackage[ruled,vlined]{algorithm2e}\n"
        "\n"
        "\\graphicspath{{figs/}}\n"
        "\\urlstyle{sf}\n"
        "\n"
        "\\usepackage{tikz}\n"
        "\\usepackage{pgfplots}\n"
        "\\usetikzlibrary{shapes,positioning,calc,snakes,arrows,shapes,fit,backgrounds}\n"
        "\n"
        "\\begin{document}\n"
        "\n"
        )
    f.write(header)

def _latex_footer(f):
    footer = (
        "\n"
        "\\end{document}\n"
        )
    f.write(footer)

def do_pgf_stacked_plot(f, tuple_data, caption='', xlabel='', ylabel='', desc='...'):
    """
    Generate PGF plot code for the given data
    @param f File to write the code to
    @param data Data points to print as list of tuples (x, y, err)
    """
    now = datetime.today()
    plotname = "%02d%02d%02d%02d%02d" % (now.year, now.month, now.day, now.hour, now.minute)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel, 
                     [ 'ybar stacked', 'ymin=0', 
                       ('legend style={'
                        ' at={(0.5,-0.20)},'
                        ' anchor=north,'
                        ' legend columns=-1'
                        '}') ], desc)

    labels = []
    for (l,data) in tuple_data:
        # Header
        f.write(("    \\addplot coordinates {\n"))
        # Data
        for d in data:
            f.write("      (%d,%f)\n" % (d[0], d[1]))
        # Footer
        f.write("    };\n");
        labels.append(l)

    f.write("     \\legend{%s}\n" % ', '.join(labels))
    _pgf_plot_footer(f)


def parse_measurement(f, coreids=None):
    """
    Parse the given file for measurements
    """

    print "parse_measurement for file %s" % f
    dic = dict()
    coresfound = []

    # If argument is a path (i.e. string), we need to open it
    if isinstance(f, basestring):
        f = open(f)

    for line in f:
        if line.startswith("sk_m"):
            d = unpack_line(clear_line(line))
            assert len(d)==4
            if coreids == None or d[0] in coreids:
                if not d[0] in dic:
                    dic[d[0]] = []
                dic[d[0]].append(d[3])
                if not d[0] in coresfound:
                    coresfound.append(d[0])
    result = []
    stat = []
    for c in coresfound:
        l = len(dic[c])
        if l > 0:
            print "core %d, length %d" % (c, len(dic[c]))
            s = statistics_cropped(dic[c])
            if s != None:
                stat.append((c, s[0], s[1]))
    return stat


def parse_and_plot_measurement(coreids, machine, topo, f):
    stat = parse_measurement(f, coreids)
    do_pgf_plot(open("../measurements/%s_%s.tex" % (machine, topo), "w+"), stat,
                "Atomic broadcast on %s with %s topology" % (machine, topo), 
                "coreid", "cost [cycles]")


def _output_table_header(f):
    f.write(("\\begin{table}[htb]\n"
             "  \\centering\n"
             "  \\begin{tabular}{lrrrrr}\n"
             "  \\toprule\n"
             "  & \\multicolumn{3}{c}{Real hardware} & \\multicolumn{2}{c}{Simulation} \\\\\n"
             "  topology & time [cycles] & factor & stderr & time [units] & factor \\\\\n"
             "  \\midrule\n"
             ))


def _output_table_footer(f, label, caption):
    f.write(("  \\midrule\n"
             "  \\end{tabular}\n"
             "  \\caption{%s}\n"
             "  \\label{tab:%s}\n"
             "\\end{table}\n") % (caption, label))


def _output_table_row(f, item, min_evaluation, min_simulation):
    assert len(item)==4
    fac1 = -1 if float(min_evaluation) == 0 else item[1]/float(min_evaluation)
    fac2 = -1 if float(min_simulation) == 0 else item[3]/float(min_simulation)
    t_sim = item[3]

    if t_sim == sys.maxint:
        t_sim = -1
        fac2 = -1

    f1 = "\colorbox{gray}{%.3f}" % fac1 if fac1 == 1.0 else "%.3f" % fac1
    f2 = "\colorbox{gray}{%.3f}" % fac2 if fac2 == 1.0 else "%.3f" % fac2

    f.write("  %s & %.2f & %s & %.2f & %.0f & %s \\\\\n" %
            (item[0], item[1], f1, item[2], t_sim, f2))

def output_machine_results(machine, res_measurement, res_simulator):
    """
    Generates a LaTeX table for the given result list.

    @param machine Name of the machine
    @param results List of (topology, mean, stderr)
    """

    if len(res_measurement)<1 or len(res_simulator)<1:
        return

    f = open('../measurements/%s_topologies.tex' % machine, 'w+')
    cap = "Evaluation of different topologies for %s" % machine

    _output_table_header(f)

    ev_times = [time for (topo, time, err) in res_measurement if time != 0]
    assert len(ev_times)>0
    min_evaluation = min(ev_times)
    min_simulation = min(time for (topo, time) in res_simulator)
    # Otherwise, the simulation didn't work
    assert min_evaluation>0 
    assert min_simulation>0 

    for e in zip(res_measurement, res_simulator):
        assert(e[0][0] == e[1][0])
        _output_table_row(f, (e[0][0], e[0][1], e[0][2], e[1][1]), 
                          min_evaluation, min_simulation)
    _output_table_footer(f, machine, cap)

def run_pdflatex(fname):
    if subprocess.call(['pdflatex', 
                     '-output-directory', '/tmp/', 
                     '-interaction', 'nonstopmode',
                        fname], cwd='/tmp') == 0:
        subprocess.call(['okular', fname.replace('.tex', '.pdf')])

def extract_machine_results(model, nosim=False):
    """
    Extract result for simulation and real-hardware from log files
    
    """
    results = []
    sim_results = []
    machine = model.get_name()
    for t in topologies:
        f = get_ab_machine_results(machine, t)

        # Real hardware
        if os.path.isfile(f):
            stat = parse_measurement(f, range(model.get_num_cores()))
            assert len(stat) == 1 # Only measurements for one core
            results.append((t, stat[0][1], stat[0][2]))
        else: 
            results.append((t, 0, 0))

        # Simulation
        if not nosim:
            try:
                (topo, ev, root, sched, topo) = \
                    simulation._simulation_wrapper(t, model, model.get_graph())
                final_graph = topo.get_broadcast_tree()
                sim_results.append((t, ev.time))
            except:
                print traceback.format_exc()
                print 'Simulation failed for machine [%s] and topology [%s]' %\
                    (machine, t)
                sim_results.append((t, sys.maxint))
        else:
            sim_results.append((t, sys.maxint))

    return (results, sim_results)

def gen_gottardo(m):

    graph = digraph()
    graph.add_nodes([n for n in range(m.get_num_cores())])
    
    for n in range(1, m.get_num_cores()):
        if n % m.get_cores_per_node() == 0:
            print "Edge %d -> %d" % (0, n)
            graph.add_edge((0, n))

    dim = m.get_num_cores()
    mat = [[0 for x in xrange(dim)] for x in xrange(dim)]
    
    import sort_longest
    sched = sort_longest.SortLongest(graph)

    # Build the matrix
    walk_graph(graph, 0, fill_matrix, mat, sched)

    stream = open("hybrid_model.h", "w")
    defstream = open("hybrid_model_defs.h", "w")
    __c_header_model_defs(defstream, 
                          m.get_num_cores()-1,
                          "",
                          "",
                          len(mat))
    __c_header_model(stream)
    __matrix_to_c(stream, mat)
    __c_footer(stream)
    __c_footer(defstream)


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
