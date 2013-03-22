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

# --------------------------------------------------

CORES_PER_NODE = 4
NUM_NUMA_NODES = 8
HOPCOST = 10

# Wrapper function to add edges between two NUMA nodes. 
def add_numa(graph, node1, node2):
    n1 = node1*CORES_PER_NODE
    n2 = node2*CORES_PER_NODE
    graph.add_edge((n1, n2), 1)

def connect_numa_nodes(g, g_numa, src):
    # assuming that routing is taking the shortes path,
    # NOT true on e.g. SCC
    cost = shortest_path(g_numa, src)[1] # don't really know what the first argument is ..
    for trg in range(len(cost)):
        if src!=trg:
            g.add_edge((CORES_PER_NODE*src, CORES_PER_NODE*trg), \
                           cost[trg]*HOPCOST)

# fully connect numa islands!
def connect_numa_internal(graph, numa_node):
    for i in range(CORES_PER_NODE):
        for j in range(CORES_PER_NODE):
            if j>i:
                node1 = numa_node*CORES_PER_NODE + i
                node2 = numa_node*CORES_PER_NODE + j
                graph.add_edge((node1, node2))

# --------------------------------------------------

# Graph creation
gr = graph()
g_numa = graph()

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

# gruyere has 32 nodes!
gr.add_nodes(range(32))

connect_numa_nodes(gr, g_numa, 0)

# # inter-numa connections
# for i in range(8):
#     connect_numa_internal(gr, i)

# Draw as PNG
dot = write(gr)
gvv = gv.readstring(dot)
gv.layout(gvv,'dot')
gv.render(gvv,'png','gruyere.png')

dot_numa = write(g_numa)
gvv_numa = gv.readstring(dot_numa)
gv.layout(gvv_numa, 'dot')
gv.render(gvv_numa, 'png', 'numa.png')
