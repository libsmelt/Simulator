# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.
# This is meant to hold all sort of configuration options

SCHEDULING_SORT=True
SCHEDULING_SORT_ID=False
SCHEDULING_SORT_LONGEST_PATH=False

topologies = [
#    "ring", 
    "cluster", 
    "mst", 
    "bintree",
    "sequential",
    "badtree",
    "adaptivetree"
    ]
machines = [
# nos6
    "ziger1",
    "gruyere",
    'sbrinz1',
# 'sbrinz2',
#    'gottardo',
    'appenzeller'
    ]

import os

def get_ab_machine_results(machine, overlay):
    return ('%s/measurements/atomic_broadcast_new_model/%s_%s' %
            (os.getenv('HOME'), machine, overlay))
