#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import socket
import sys
import json
import helpers
import config
import threading
import logging

from io import StringIO

PORT=25041


class SimArgs:
    """This is for passing arguments to the simulate function

    In none-server-mode, this is extracted from the arguments
    parsed with argparse"""

    multicast = True
    hybrid = False
    hybrid_cluster = 'NUMA'
    machine = None
    overlay = None
    group = []
    multimessage = False
    reverserecv = False


class ClientThread(threading.Thread):

    def __init__(self, address, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        print ('connection from', address)

    def run(self):

        try:
            # Receive the data in small chunks and retransmit it
            buf = StringIO()

            # XXX properly detect the length of the message
            # here and receive ALL of it.
            data = self.socket.recv(10240)
            print(data.decode('ascii'))
            
            buf.write(data.decode('ascii'))

            # There is still no guarantee that this is
            # correct, but if not, the json parser will fail.

            assert len(data)<10240 # Otherwise, the message is
                                   # longer than 10240 and we
                                   # need to properly
                                   # implement sockets

            res = handle_request(json.loads(buf.getvalue()))
            if len(res)>0:
                self.socket.sendall(res.encode('ascii'))

        finally:
            # Clean up the connection
            self.socket.close()

        print ("Client disconnected...")


def handle_request(r):
    """Handle the Simulator request given by the r dictionary
    """
    print ("handle_request executed .. ")
    print (r)

    # Parse request ..
    config = SimArgs()
    config.machine = r[u'machine']
    config.overlay = [r[u'topology']] # List of topologies - just one
    config.group = r[u'cores']
    overlay = r[u'topology'].split('-')

    overlay_name = overlay[0]
    overlay_args = overlay[1:]

    if overlay_name == 'hybrid':
        overlay_name = 'cluster'
        config.hybrid = True;
        config.hybrid_cluster = overlay_args[0];
        config.overlay = [u'cluster']

    if overlay_args == 'mm' :
        config.multimessage = True
    elif overlay_args == 'rev' :
        config.reverserecv = True

    c = config

    from simulator import simulate
    (last_nodes, leaf_nodes, root) = simulate(config)

    # Generate response to be sent back to client
    import config
    assert len(config.models)==1 # Exactly one model has been generated

    res = {}
    res['root'] = root
    res['model'] = config.models[0]
    res['last_node'] = last_nodes[0]
    res['leaf_nodes'] = leaf_nodes[0]
    res['git-version'] = helpers.git_version().decode('ascii')

    print(res)

    logging.info(('Responding with >>>'))
    logging.info((json.dumps(res)))
    logging.info(('<<<'))

    write_statistics(c.machine)

    return json.dumps(res)


STAT_FILE = 'statistics.json'
def write_statistics(machine):

    # Read
    try:
        with open(STAT_FILE, 'r') as f:
            stat = json.loads(f.read())
            f.close()
    except IOError:
        stat = {}

    # Update
    stat['num_served'] = stat.get('num_served', 0) + 1
    stat['num_served_%s' % machine] = stat.get('num_served_%s' % machine, 0) + 1


    # Write
    f = open(STAT_FILE, 'w')
    json.dump(stat, f)


def server_loop():

    config.running_as_server = True
    print ('Starting server')

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('', PORT) # empty string = accept from all addresses
    print ('starting up on %s port %s' % server_address)
    sock.bind(server_address)

    sock.listen(1)

    try:

        while True:
                # Wait for a connection
                print ('waiting for a connection')
                connection, client_address = sock.accept()

                # Handle client connection in a separate thread
                t = ClientThread(client_address, connection)
                t.start()


    finally:
        # Cleanup sockets
        print ("Closing socket .. ")
        # sock.shutdown(1)
        # sock.close()
