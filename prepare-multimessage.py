#!/usr/bin/python

import sys

from config import MACHINE_DATABASE
MDB= '%s/' % MACHINE_DATABASE

sys.path.append(MDB)
import machineinfo


def prepare_multimessage(machine):

    root = 0
    assert root in machine.get_cores()

    num_nodes = machine.get_num_numa_nodes()

    local = [ str(l) for l in machine.get_numa_node(root) if l != root ]

    cores =  [ (c, machine.get_send_cost(root, c)) for c in machine.get_cores()]
    cores = sorted(cores, key=lambda x: x[1], reverse=True)

    node_avg = []

    for idx, node in enumerate(machine.get_numa_information()):
        if machine.get_numa_id(root) == idx:
            continue
        node_avg += [(idx, sum([ machine.get_send_cost(root, c) for c in node ])/len(node))]

    node_avg = sorted(node_avg, key=lambda x: x[1], reverse=True)[:2]
    n1 = machine.get_numa_node_by_id(node_avg[0][0])


    if num_nodes>2:

        n2 = machine.get_numa_node_by_id(node_avg[1][0])

        # http://stackoverflow.com/questions/3471999/how-do-i-merge-two-lists-into-a-single-list
        remote = [str(j) for i in zip(n1,n2) for j in i]

    else:
        remote = [str(j) for j in n1]


    s = ('%s)\n'
         '  ARGS=\"%d %s %s\"\n'
         '  ;;') % (machine.get_name(), root, ','.join(local), ','.join(remote))

    print >> sys.stderr,  s


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--machines')

global arg
arg = parser.parse_args()

import machineinfo
all_machines = [ s for (s, _, _) in machineinfo.machines ]
machines = all_machines if not arg.machines else arg.machines.split()

for m in machines:
    try:

        # Initialize machine to get pairwise send costs
        import config
        from netos_machine import NetosMachine
        from server import SimArgs

        # Set machine name
        config.args = SimArgs()
        config.args.machine = m

        m_class = NetosMachine()
        prepare_multimessage(m_class)

    except IOError as e:
        print str(e)

exit(0)
