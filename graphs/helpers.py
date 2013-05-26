# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv
import Queue
from numpy import *
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


def output_quorum_configuration(model, graph, root, sched):
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
    __c_header(stream, model.evaluation.last_node)
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


def __c_header(stream, last_node):
    stream.write("#ifndef MULTICORE_MODEL\n")
    stream.write("#define MULTICORE_MODEL 1\n\n")
    stream.write("#define LAST_NODE %d\n\n" % last_node)


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

def statistics(l):
    """
    Print statistics for the given list of integers
    @return A tuple (mean, stderr, min, max)
    """
    if not isinstance(l, list) or len(l)<1:
        return None
    nums = array(l)

    m = nums.mean(axis=0)
    d = nums.std(axis=0)

    return (m, d, nums.min(), nums.max())


def _pgf_plot_header(f, plotname, caption, xlabel, ylabel):
    label = "pgfplot:%s" % plotname
    s = (("Plot~\\ref{%s} shows ...\n"
          "\\begin{figure}\n"
          "  \\caption{%s}\n"
          "  \\label{%s}\n"
          "  \\begin{tikzpicture}\n"
          "    \\begin{axis}[\n"
          "        xlabel={%s},\n"
          "        ylabel={%s}\n"
          "        ]\n") % (label, caption, label, xlabel, ylabel))
    f.write(s)


def _pgf_plot_footer(f):
    s = ("    \\end{axis}\n"
         "  \\end{tikzpicture}\n"
         "\\end{figure}\n")
    f.write(s)

    
def do_pgf_plot(f, data, caption, xlabel, ylabel):
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


def parse_measurement(coreids, machine, topo, f):
    """
    Parse the given file for measurements
    """
    dic = dict()
    for c in coreids:
        dic[c] = []
    for line in open(f):
        if line.startswith("sk_m"):
            d = unpack_line(clear_line(line))
            assert len(d)==4
            if d[0] in coreids:
                dic[d[0]].append(d[3])
    result = []
    stat = []
    for c in coreids:
        s = statistics(dic[c])
        if s != None:
            stat.append((c, s[0], s[1]))
    do_pgf_plot(open("../measurements/%s_%s.tex" % (machine, topo), "w+"), stat,
                "Atomic broadcast on %s with %s topology" % (machine, topo), 
                "coreid", "cost [cycles]")
                

    
