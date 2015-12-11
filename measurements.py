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
import ziger
import sbrinz
import appenzeller

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

# --------------------------------------------------
def evaluate_file():
    """
    Build a tree model and simulate sending a message along it
    """
    parser = argparse.ArgumentParser(
        description='Parse measurements for multicore machines')
    parser.add_argument(
        'infile', 
        type = argparse.FileType('r'), 
        nargs = '?', 
        default = sys.stdin,
        help='File to parse or stdin'
        )
    args = parser.parse_args()

    print helpers.parse_measurement(args.infile)

if __name__ == "__main__":
    evaluate_file()
