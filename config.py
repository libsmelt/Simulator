# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.
# This is meant to hold all sort of configuration options

import os

topologies = [
    "adaptivetree",
    "mst",
    "bintree",
    "cluster",
    "badtree",
    "fibonacci",
    "sequential",
    ]

machines = []


# List of models that have been generated - this is needed (currently)
# to make generated models available for sending back to the
# requesting client when acting as a RPC server.
models = []
running_as_server = False

# Find config.py's working directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# Path to the machine database.
MACHINE_DATABASE='%s/machinedb/' % dir_path

# Arguments as given when invoking the simulator
args = None

def translate_machine_name(n):
    """
    """
    return n


def arg_machine_class(machine):
    """
    """
    import netos_machine
    return netos_machine.NetosMachine


def arg_machine(machine_name):
    """
    Return instance of the machine given as argument

    """
    machine_name = translate_machine_name(machine_name)

    if machine_name == 'rack':
        raise Exception('Racks not currently supported')

    else:
        return arg_machine_class(machine_name)

def get_mc_group():
    assert args.group
    return args.group
