#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import socket
import json
import server
import argparse

from StringIO import StringIO

PORT=server.PORT

def main():
    # Parse configuration from arguments
    p = argparse.ArgumentParser(description=('Test Simulator when running as a server'))
    p.add_argument('machine')
    p.add_argument('topology')
    p.add_argument('cores', help='Cores to generate the topology for (as comma separated list of ranges, e.g. 1,2,3-4,5)')
    a = p.parse_args()

    # Parse cores
    cc = a.cores.split(',')
    cores = []
    for ccc in cc:
        if '-' in ccc:
            e = ccc.split('-')
            cores += range(int(e[0]), int(e[1])+1)
        else:
            cores += [ int(ccc) ]

    print 'Requsting:', a.machine, a.topology, str(a.cores), '->', cores

    # Open connection to Simulator server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', PORT))

    # Prepare request
    req = {}
    req['machine'] = a.machine
    req['topology'] = a.topology
    req['cores'] = cores

    # Send request
    req_msg = json.dumps(req)
    s.sendall(req_msg)

    # Receive request
    buf = StringIO()

    while True:
        data = s.recv(1024)
        buf.write(data)

        if len(data)<1:
            print 'Server connection closed, transmission done'
            break

    # Convert to json object
    res = json.loads(buf.getvalue())
    print 'Machine model is of size', len(res['model']), len(res['model'][0])

    s.close()

if __name__ == "__main__":

    main()
    exit(0)
