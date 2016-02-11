# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.
# This is meant to hold all sort of configuration options

import os

SCHEDULING_SORT=True
SCHEDULING_SORT_ID=False
SCHEDULING_SORT_LONGEST_PATH=False
USE_UMP_NUMA=False
USE_UMPQ=False

topologies = [
#    "ring",
    "adaptivetree",
    "mst",
    "bintree",
    "cluster",
    "badtree",
    "fibonacci",
    "sequential",
    ]
machines = [
    ]


# List of models that have been generated - this is needed (currently)
# to make generated models available for sending back to the
# requesting client when acting as a RPC server.
models = []

# Path to the machine database.
MACHINE_DATABASE=os.getenv('HOME') + '/projects/netos-machine-hardware-information'

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
    """Remove digits from machine name unless machine is a sgs machine
    """
    return n
    # return n if n.startswith('sgs') else \
    #     ''.join([i for i in n if not i.isdigit()])


def arg_machine_class(machine):
    """

    """
    import netos_machine
    return netos_machine.NetosMachine
    



def arg_machine(machine_name):
    """
    Return instance of the machine given as argument

    """
    import rack
    machine_name = translate_machine_name(machine_name)

    if machine_name == 'rack':
        raise Exception('Racks not currently supported')

    else:
        return arg_machine_class(machine_name)

def get_mc_group():
    assert args.group
    return args.group
