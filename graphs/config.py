# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.
# This is meant to hold all sort of configuration options

SCHEDULING_SORT=True
SCHEDULING_SORT_ID=False
SCHEDULING_SORT_LONGEST_PATH=False
USE_UMP_NUMA=False
USE_UMPQ=True

topologies = [
#    "ring", 
    "cluster", 
    "mst", 
    "bintree",
#    "sequential", SK: Can't predict this very closely right now due to the write-buffer
    "badtree",
    "fibonacci",
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

def result_suffix():
    return _result_suffix(USE_UMP_NUMA, USE_UMPQ)


def _result_suffix(numa, umpq):
    if umpq:
        return '_UMPQ'
    elif numa:
        return '_NUMA'
    else:
        return '_noNUMA'

import os

# Arguments as given when invoking the simulator
args = None

# Set these manually
# --------------------------------------------------
MULTICAST_RATIO=.5 # Probability for each node to be used for the multicast.

def get_ab_machine_results(machine, overlay, flounder=False, umpq=False):
    machine = ''.join([i for i in machine if not i.isdigit()])

    suffix = get_machine_result_suffix(flounder, umpq)

    return ('%s/measurements/atomic_broadcast_new_model/%s_%s%s' %
            (os.getenv('HOME'), machine, overlay, suffix))

def get_machine_result_suffix(flounder, umpq):
    assert not flounder or not umpq
    suffix = ''
    if flounder:
        suffix = '_flounder'
    elif umpq:
        suffix = '_UMPQ'
    return suffix


def translate_machine_name(n):
    return ''.join([i for i in n if not i.isdigit()])


def arg_machine_class(string):
    """

    """
    # Machines
    import gruyere
    import nos6
    import ziger
    import sbrinz
    import gottardo
    import appenzeller
    import tomme

    if string == "gruyere":
        return gruyere.Gruyere
    elif string == "nos":
        return nos6.Nos
    elif string == 'ziger':
        return ziger.Ziger
    elif string == 'sbrinz':
        return sbrinz.Sbrinz
    elif string == 'gottardo':
        return gottardo.Gottardo
    elif string == 'appenzeller':
        return appenzeller.Appenzeller
    elif string == 'tomme':
        return tomme.Tomme
    else:
        raise Exception('Unknown machine')
    

def arg_machine(machine_name):
    """
    Return instance of the machine given as argument

    """
    import rack
    machine_name = translate_machine_name(machine_name)

    if machine_name == 'rack':
        return rack.Rack(sbrinz.Sbrinz)

    else:
        return arg_machine_class(machine_name)
