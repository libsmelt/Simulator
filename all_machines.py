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

import netos_machine
import config

from server import SimArgs

def main():
    for machine in netos_machine.get_list():
        config.args = SimArgs()
        config.args.machine = machine
        m_class = config.arg_machine(machine)

        try:
            m = m_class()
            r = m.get_receive_send_ratio()
            print 'Machine %20s - ratio is: %5.2f %5.2f %5.2f ' % \
                (machine, r[0], r[1], r[2])

        except IOError:
            print 'Could not load machine'



if __name__ == "__main__":
    main()
