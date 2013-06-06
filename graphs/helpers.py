# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv
import Queue
import numpy
from datetime import *

from pygraph.readwrite.dot import write
from pygraph.algorithms.minmax import shortest_path

def output_graph(graph, name, algorithm='neato'):
    """
    Output the graph as png image and also as text file
    """
    dot = write(graph, True)
    gvv = gv.readstring(dot)
    
    with open('%s.dot'%name, 'w') as f:
        f.write(dot)

    gv.layout(gvv, algorithm)
    gv.render(gvv, 'png', ('%s.png' % name))


def output_quorum_configuration(model, graph, root, sched, topo):
    """
    Output a C array representing overlay and scheduling
    """
    
    dim = model.get_num_cores()
    mat = [[0 for x in xrange(dim)] for x in xrange(dim)]

    # Build the matrix
    walk_graph(graph, root, fill_matrix, mat, sched)

    # Determine longest path with most expensive node
    sp = shortest_path(graph, root)[1].items()
    sp.sort(key=lambda tup: tup[1], reverse=True)

    # Generate c code
    stream = open("model.h", "w")
    __c_header(stream, model.evaluation.last_node, type(model), type(topo))
    __matrix_to_c(stream, mat)
    __c_footer(stream)


def walk_graph(graph, root, func, mat, sched):
    """
    Function to walk the tree starting from root

    active = reachable, but not yet dealt with. Elements are tuples (node, parent)
    done = reachable and also handled
    """
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
        for nb in graph.neighbors(a):
            if not nb in done:
                active.put((nb, a))
                nbs.append(nb)

        # call handler function
        func(a, nbs, parent, mat, sched)
        

def fill_matrix(s, children, parent, mat, sched):
    """
    """
    i = 1
    for (cost, r) in sched.find_schedule(s):
        if r in children:
            mat[s][r] = i
            i += 1
    if not parent == None:
        assert len(children)<90
        mat[s][parent] = 99


def __matrix_to_c(stream, mat):
    """
    Print given matrix as C code
    """
    dim = len(mat)
    stream.write(("#define MODEL_NUM_CORES %d\n\n" % dim))
    stream.write(("int model[%d][%d] = {\n" % (dim, dim)))
    for x in range(dim):
        stream.write("    {")
        for y in range(dim):
            stream.write("%2d" % mat[x][y])
            if y+1 != dim:
                stream.write(",")
        stream.write("}")
        if x+1 != dim:
            stream.write(",")
        stream.write("\n")
    stream.write("};\n\n")


def __c_header(stream, last_node, machine, topology):
    stream.write('#ifndef MULTICORE_MODEL\n')
    stream.write('#define MULTICORE_MODEL 1\n\n')
    stream.write('#define MACHINE "%s"\n' % machine)
    stream.write('#define TOPOLOGY "%s"\n' % topology)
    stream.write('#define LAST_NODE %d\n\n' % last_node)


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


def _pgf_plot_header(f, plotname, caption, xlabel, ylabel, attr=[], desc='...'):
    label = "pgfplot:%s" % plotname
    s = (("Plot~\\ref{%s} shows %s\n"
          "\\pgfplotsset{width=\linewidth}\n"
          "\\begin{figure}\n"
          "  \\caption{%s}\n"
          "  \\label{%s}\n"
          "  \\begin{tikzpicture}\n"
          "    \\begin{axis}[\n"
          "        %s,\n" 
          "        xlabel={%s},\n"
          "        ylabel={%s}\n"
          "        ]\n") % (label, desc, caption, label, ','.join(attr), xlabel, ylabel))
    f.write(s)


def _pgf_plot_footer(f):
    s = ("    \\end{axis}\n"
         "  \\end{tikzpicture}\n"
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
        "\\usetikzlibrary{shapes,positioning,calc,snakes,arrows,shapes}\n"
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
            assert len(dic[c])==100
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
    f.write("  %s & %.2f & %.3f & %.2f & %.0f & %.3f \\\\\n" %
            (item[0], item[1], item[1]/float(min_evaluation), item[2], 
             item[3], item[3]/float(min_simulation)))

def output_machine_results(machine, res_measurement, res_simulator):
    """
    Generates a LaTeX table for the given result list.

    @param machine Name of the machine
    @param results List of (topology, mean, stderr)
    """
    f = open('../measurements/%s_topologies.tex' % machine, 'w+')
    cap = "Evaluation of different topologies for %s" % machine

    _output_table_header(f)
    min_evaluation = min(time for (topo, time, err) in res_measurement)
    min_simulation = min(time for (topo, time) in res_simulator)
    for e in zip(res_measurement, res_simulator):
        assert(e[0][0] == e[1][0])
        _output_table_row(f, (e[0][0], e[0][1], e[0][2], e[1][1]), 
                          min_evaluation, min_simulation)
    _output_table_footer(f, machine, cap)
