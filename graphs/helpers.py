# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

# Import graphviz
import sys
sys.path.append('..')
sys.path.append('/usr/lib/graphviz/python/')
sys.path.append('/usr/lib64/graphviz/python/')
import gv

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


