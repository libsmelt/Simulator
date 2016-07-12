# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv
import logging

# Import pygraph
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph
from pygraph.algorithms.searching import breadth_first_search
from pygraph.readwrite.dot import write
from pygraph.algorithms.minmax import shortest_path
from pygraph.algorithms.minmax import minimal_spanning_tree

# Import own code
import evaluate
import model
import helpers
import algorithms
import overlay

class Fibonacci(overlay.Overlay):
    """
    Build a cluster topology for a model
    """
    
    def __init__(self, mod):
        """
        Initialize the clustering algorithm
        """
        super(Fibonacci, self).__init__(mod)

    def get_name(self):
        return "fibonacci"

        
    def _build_tree(self, g):
        """
        Return the broadcast tree as a graph
        """

        num_cores = len(g.nodes())

        # Find fibonacci number such that the tree is big enough 
        # See http://xlinux.nist.gov/dads/HTML/fibonacciTree.html 
        # Number of nodes in a Fibonacci tree of size i (without "0"-nodes)
        # is F(i+2)-1
        fibno = 0
        while algorithms.F(fibno+2)-1<num_cores:
            fibno += 1

        print 'Fibonacci number for this machine is %d' % fibno

        # Build tree
        nodes = []
        edges = []
        algorithms.fibonacci(fibno, nodes, edges)

        assert len(nodes)>=num_cores
        
        # Sort nodes such that nodes further up in the tree come first
        nodes = sorted(nodes, cmp=lambda x, y: cmp(len(x),len(y)))

        # Shorten nodes so that we have just enough cores
        nodes = nodes[:num_cores]

        # Build dictionary with node name translations
        d = {}
        cores = sorted(g.nodes())

        for (n, idx) in zip(nodes, cores):
            d[n] = idx

        # Build tree
        g = digraph()
        for n in [ d[key] for key in nodes ]:
            g.add_node(n)

        for (s,e) in edges:
            if s in d and e in d:
                g.add_edge((d[s],d[e]))


        return g
