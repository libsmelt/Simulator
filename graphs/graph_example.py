#!/usr/bin/env python

# Copyright (c) 2007-2008 Pedro Matiello <pmatiello@gmail.com>
# License: MIT (see COPYING file)

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv

# Import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.readwrite.dot import write
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.minmax import minimal_spanning_tree

# --------------------------------------------------

CORES_PER_NODE = 4
NUM_NUMA_NODES = 8
NUM_CORES = (CORES_PER_NODE*NUM_NUMA_NODES)
HOPCOST = 10
NUMACOST = 1

def output_graph(graph, name):
    """
    Output the graph as png image and also as text file
    """
    dot = write(graph, True)
    gvv = gv.readstring(dot)
    
    with open('%s.dot'%name, 'w') as f:
        f.write(dot)

    gv.layout(gvv, 'neato')
    gv.render(gvv, 'png', ('%s.png' % name))


# Wrapper function to add edges between two NUMA nodes. 
def add_numa(graph, node1, node2, cost):
    n1 = node1*CORES_PER_NODE
    n2 = node2*CORES_PER_NODE
    for c1 in range(CORES_PER_NODE):
        for c2 in range(CORES_PER_NODE):
            src = (n1+c1)
            dest = (n2+c2)
            if src < dest:
                print "Adding edge %d -> %d with weight %d" % \
                    (src, dest, cost)
                graph.add_edge((src, dest), cost)

def connect_numa_nodes(g, g_numa, src):
    # assuming that routing is taking the shortes path,
    # NOT true on e.g. SCC
    connect_numa_internal(g, src)
    cost = shortest_path(g_numa, src)[1] # don't really know what the first argument is ..
    print "connect numa nodes for %d: cost array size is: %d" % \
        (src, len(cost))
    for trg in range(len(cost)):
        if src!=trg:
            add_numa(g, src, trg, cost[trg]*HOPCOST)

# fully connect numa islands!
def connect_numa_internal(graph, numa_node):
    for i in range(CORES_PER_NODE):
        for j in range(CORES_PER_NODE):
            if j>i:
                node1 = numa_node*CORES_PER_NODE + i
                node2 = numa_node*CORES_PER_NODE + j
                graph.add_edge((node1, node2), NUMACOST)

# --------------------------------------------------

# Graph creation
gr = graph()
g_numa = graph()

dbg_num_edges = 0
for n in range(NUM_CORES):
    dbg_num_edges += n

print "Expecting %d edges" % dbg_num_edges

# --------------------------------------------------
# Construct graph of NUMA nodes

g_numa.add_nodes(range(NUM_NUMA_NODES))

for i in range(3):
    g_numa.add_edge((i, i+1)) # to right, top row
    g_numa.add_edge((i, i+4)) # top to bottom row

for i in range(4,7):
    g_numa.add_edge((i, i+1)) # to right, bottom row

# remainig edges
g_numa.add_edge((2,7))
g_numa.add_edge((3,6))
g_numa.add_edge((3,7))

# --------------------------------------------------
# Build fully meshed machine graph

gr.add_nodes(range(NUM_CORES))

for n in range(NUM_NUMA_NODES):
    connect_numa_nodes(gr, g_numa, n)

# --------------------------------------------------
# Run MST algorithm
mst = graph()
mst.add_nodes(range(NUM_CORES))

mst_edges = minimal_spanning_tree(gr)
for i in range(len(mst_edges)):
    if mst_edges[i] != None:
        mst.add_edge((mst_edges[i], i), \
                         gr.edge_weight((mst_edges[i], i)))

# --------------------------------------------------

output_graph(gr, 'gruyere')
output_graph(g_numa, 'numa')
output_graph(mst, 'mst')
