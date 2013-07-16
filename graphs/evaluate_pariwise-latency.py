#!/usr/bin/env python

import sys
import fileinput
import re

sys.path.append('/home/skaestle/bf/quorum/tools/harness')
sys.path.append('/home/skaestle/bf/quorum/tools/harness/tests')
sys.path.append('/home/skaestle/bf/quorum/tools/harness/machines')

sys.path.append('/home/skaestle/bin/')

import helpers
import argparse

parser = argparse.ArgumentParser(
    description='Evaluation of UMP')
parser.add_argument('--machine', default='unknown')
args = parser.parse_args()

r = []

for line in sys.stdin.readlines():
    line = line.rstrip()
    if not re.match('^[0-9]', line):
        continue
    ls = line.split()
    if not len(ls)>=3:
        continue
    (x, y, z) = map(float, (ls[0], ls[1], ls[2]))
    r.append((x,y,z))

r = sorted(r, key = lambda x : (x[1], x[0]))
last = -1

fname_res = '/tmp/res.dat'
f_res = open(fname_res, 'w+')

for (x,y,z) in r:
    if y != last:
        f_res.write('\n')
        last = y
    f_res.write('%d %d %f\n' % (x,y,z))

f_res.close()

fname = '/tmp/plot3.tex'
f = open(fname, 'w+')

helpers._latex_header(f)
helpers.do_pgf_3d_plot(f, fname_res, 
                       'pair-wise latency for %s' % args.machine, 
                       'sending core', 'receiving core', 'cost [cycles]')
helpers._latex_footer(f)

f.close()

helpers.run_pdflatex(fname)
