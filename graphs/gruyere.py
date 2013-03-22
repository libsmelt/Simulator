#!/usr/bin/env python

CORES_PER_NUMA_NODE=8

def is_same_numa_node(c1, c2):
    return c1/CORES_PER_NUMA_NODE == c2/CORES_PER_NUMA_NODE

