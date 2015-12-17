#!/usr/bin/env python

# Import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.minmax import minimal_spanning_tree

# Import own code
import evaluate
import config
import model
import helpers
import algorithms

# Overlays
import cluster
import ring
import binarytree
import sequential
import badtree

import scheduling
import sort_longest

import pdb
import argparse
import logging
import sys
import os

# helpers.output_machine_results("testmachine", 
#                                [(100, 5), (200, 10), (300, 15)], 
#                                [(10, 5.5), (20, 10.1), (30, 12.3)]
#                                )

# Number of nodes in Fibonacci tree:
# http://xlinux.nist.gov/dads/HTML/fibonacciTree.html
# F(i+2)-1 for Fibonacci tree of size i
for i in range(11):
    nodes = []
    edges = []
    fibno = algorithms.F(i+2) - 1
    algorithms.fibonacci(i, nodes, edges)
    print "%d %d %d" % (i, len(nodes), fibno)

NUM_NODES = 32

nodes = []
edges = []
algorithms.fibonacci(7, nodes, edges)

f = open('/tmp/fibonacci.dot', 'w+')
f.write('digraph {\n')

nodes = sorted(nodes, cmp=lambda x, y: cmp(len(x),len(y)))

for (idx, n) in enumerate(nodes):
    if idx<NUM_NODES:
        attr = ['fillcolor=palegreen','style=filled','label="core %d"' % idx]
    else:
        attr = ['label="unused %d"' % (idx-NUM_NODES)]
    f.write('%s [%s];\n' % (n,','.join(attr)));

for (s,e) in edges:
    f.write('%s -> %s;\n' % (s,e))

f.write('}\n')
f.close
