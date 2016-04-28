#!/usr/bin/env python

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

import subprocess
import tools

def main():
    import config

    sys.path.append(config.MACHINE_DATABASE)
    from machineinfo import machines

    out = []

    for s in [ s for (s, _, _) in machines ]:
        cmd = ['./simulator.py', s, 'adaptivetree-optimized'] #, '--visu']

        res = []

        try:
            for l in subprocess.check_output(cmd, stderr=subprocess.STDOUT).split('\n'):

                if l.startswith('Cost'):
                    e = l.split(':')[1].split()
                    res_feedback = int(e[0]) # This is the result including the feedback edge leaf->root
                    res_real = int(e[1].strip("(),"))
                    res.append(res_real)

            bla = (s, res[0], res[1], float(res[1])/res[0]) #, res[2])
            out.append(bla)
            print '%-30s %6d %6d %5.2f' % bla

        except subprocess.CalledProcessError:
            print s, 'failed'
        except:
            raise


if __name__ == "__main__":
    main()
