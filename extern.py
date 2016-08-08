#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

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

m = config.arg_machine_class(args.machine)(config.args.multimessage, config.args.reverserecv)
n = int(args.iteration)
print "Using machine [%s] with [%d] cores, generating group of [%d]" % \
    (m.get_name(), m.get_num_cores(), n)

if n>m.get_num_cores():
    exit(1)

c = sorted(get_group(m, n))

print ','.join(map(str, c))
exit(0)
