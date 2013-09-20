#!/usr/bin/env python

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

import helpers
import config

def get_group(machine, num):
    """
    """
    cores = []
    idx = 0
    r = 0
    while num>0:
        assert r<machine.get_cores_per_node()
        cores.append(idx)
        idx += machine.get_cores_per_node()
        if idx>=machine.get_num_cores():
            r += 1
            idx = r
        num -= 1
    return cores

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('machine')
parser.add_argument('iteration')
args = parser.parse_args()

m = config.arg_machine_class(args.machine)()
n = int(args.iteration)
print "Using machine [%s] with [%d] cores, generating group of [%d]" % \
    (m.get_name(), m.get_num_cores(), n)

if n>m.get_num_cores():
    exit(1)

c = sorted(get_group(m, n))

print ','.join(map(str, c))
exit(0)






