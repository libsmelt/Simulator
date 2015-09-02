#!/usr/bin/env python

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

import tools
import fileinput
import re

# Running send between core 0 and core 1
# page 12 took 21

def main():

    curr = None
    buf = {}

    for line in fileinput.input():

        m = re.match('Running (\S+) between core (\d+) and core (\d+)', line)
        if m:
            (title, s, r) = m.group(1), m.group(2), m.group(3)
            curr = (s, r)

            buf[curr] = []
            buf[(s,s)] = [-1]

        m = re.match('page (\d+) took (\d+)', line)
        if m:
            assert curr
            buf[curr].append(m.group(2))

    for ((s,r), v) in buf.items():
        (mean, stderr, _, _, _) = tools.statistics_cropped(map(int,v), .2)
        print s, r, mean, stderr


if __name__ == "__main__":
    main()
