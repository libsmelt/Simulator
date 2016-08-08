#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import networkx as nx
import matplotlib.pyplot as plt
import pylab
import re
import fileinput

G = nx.DiGraph()

def output(l):
    """
    Parse output line

    """
    global G

    print l.rstrip()

    if re.match('^NODE: \d+', l):
        v = l.split()
        n = int(v[1])
        G.add_node(n);
        print 'adding node %d' % n
        return True

    elif re.match('^EDGE: \d+ -> \d+', l):
        (_, n1, _, n2) = l.split()
        n1 = int(n1)
        n2 = int(n2)
        G.add_edge(n1, n2)
        print 'adding edge %d ->  %d' % (n1, n2)
        return True

    return False

def draw_loop():
    """
    Draw the graph in a loop

    """
    global G

    plt.ion()

    # mng = plt.get_current_fig_manager()
    # mng.resize(*mng.window.maxsize())
    plt.draw()

    for line in fileinput.input():
        if output(line):
            plt.clf()
            nx.draw(G)
            plt.draw()

print "Enabling interactive mode"
pylab.ion()

draw_loop()
