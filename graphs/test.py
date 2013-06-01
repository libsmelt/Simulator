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

# Machines
import gruyere
import nos6

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

import ziger

# z = ziger.Ziger()
# print z.get_numa_information()


helpers.output_machine_results("testmachine", 
                               [(100, 5), (200, 10), (300, 15)], 
                               [(10, 5.5), (20, 10.1), (30, 12.3)]
                               )
