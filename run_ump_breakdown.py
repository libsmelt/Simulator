#!/usr/bin/env python

import sys

sys.path.append('/home/skaestle/bf/quorum/tools/harness')
sys.path.append('/home/skaestle/bf/quorum/tools/harness/tests')
sys.path.append('/home/skaestle/bf/quorum/tools/harness/machines')

# from eth_machinedata import machines

# for (key, m) in machines.items():
#     print '%s -> %s' % (key, m.get('machine_name'))

import ump_latency
import results

l = ump_latency.UMPLatency(None)
r = l.process_data(None, open('/dev/stdin'))

r.to_file(open('/dev/stdout', 'w'))

# rows = sorted(r.rows, key=lambda x: (x[1], x[0]))

# last = -1
# for (x,y,z,_) in rows:
#     if last != y:
#         print ''
#         last = y
#     print '%d %d %f' % (x,y,z)


