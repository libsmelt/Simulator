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

import subprocess

def main():
    import config

    sys.path.append(config.MACHINE_DATABASE)
    from machineinfo import machines

    topos = [ 'adaptivetree-min', \
              'adaptivetree-shuffle', \
              'adaptivetree-shuffle-sort' ] # Don't include adaptivetree itself

    print 'machine                           adaptiv   ',
    for t in topos:
        print '%-15s ' % (t.replace('adaptivetree', 'a')),
    print ''

    for s in [ s for (s, _, _) in machines ]:

        res = {}
        complete = True

        # ridx is the index of the Cost output to be considered.
        #
        # 0 is normally ab, 1 reduction, 2 barriers, but in some
        # cases, ab is executed twice and we actually want index 1
        # (i.e. the second cost)
        for t in topos + [ 'adaptivetree' ]:

            cmd = [ './simulator.py', s, t ] #, '--visu']

            try:
                for l in subprocess.check_output(cmd, stderr=subprocess.STDOUT).split('\n'):
                    if l.startswith('Cost atomic broadcast'):
                        e = l.split(':')[1].split()
                        res[t] = int(e[1].strip("(),"))

            except subprocess.CalledProcessError:
                complete = False
            except:
                raise

        # --------------------------------------------------

        if not 'adaptivetree' in res:
            continue

        # Print machine name
        print '%-30s ' % s,

        if complete:

            # Print cost of basic adaptive tree
            baseline = res['adaptivetree']
            print '%6d' % baseline,

            for t in topos:
                cost = res[t]
                factor = float(cost)/float(baseline)
                print '    %6d %5.2f' % (cost, factor),

        print ''


if __name__ == "__main__":
    main()
