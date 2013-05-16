# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv

import Queue

from pygraph.readwrite.dot import write


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
    # for s in range(dim):
    #     i = 1
    #     for (cost,r) in sched.find_schedule(s):
    #         mat[s][r] = i
    #         i += 1
    walk_graph(graph, root, fill_matrix, mat, sched)
    __matrix_to_c(mat)


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


def __matrix_to_c(mat):
    """
    Print given matrix as C code
    """
#    stream = sys.stdout
    stream = open("model.h", "w")
    dim = len(mat)
    stream.write("#ifndef MULTICORE_MODEL\n")
    stream.write("#define MULTICORE_MODEL 1\n\n")
    stream.write(("#define MODEL_NUM_CORES %d\n\n" % dim))
    stream.write(("int model[%d][%d] = {\n" % (dim, dim)))
    for x in range(dim):
        stream.write("    {")
        for y in range(dim):
            stream.write("%d" % mat[x][y])
            if y+1 != dim:
                stream.write(",")
        stream.write("}")
        if x+1 != dim:
            stream.write(",")
        stream.write("\n")
    stream.write("};\n\n")
    stream.write("#endif\n")


