#!/usr/bin/env python

import socket
import sys
import json

from StringIO import StringIO

PORT=25041


class SimArgs:
    """This is for passing arguments to the simulate function

    In none-server-mode, this is extracted from the arguments 
    parsed with argparse"""
    
    multicast = True
    hybrid = False
    machine = None
    overlay = None
    group = []


def handle_request(r):
    """Handle the Simulator request given by the r dictionary
    """
    print "handle_request executed .. "
    print r

    # Parse request .. 
    config = SimArgs()
    config.machine = r[u'machine']
    config.overlay = [r[u'topology']] # List of topologies - just one
    config.group = r[u'cores']

    from simulator import simulate
    (last_nodes, leaf_nodes) = simulate(config)

    # Generate response to be sent back to client
    import config
    assert len(config.models)==1 # Exactly one model has been generated

    res = {}
    res['model'] = config.models[0]
    res['last_node'] = last_nodes[0]
    res['leaf_nodes'] = leaf_nodes[0]

    print 'Responding with >>>'
    print json.dumps(res)
    print '<<<'
    
    return json.dumps(res)
        
    

def server_loop():
    print 'Starting server'

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_address = ('localhost', PORT)
    print >>sys.stderr, 'starting up on %s port %s' % server_address
    sock.bind(server_address)

    sock.listen(1)

    try:
    
        while True:
                # Wait for a connection
                print >>sys.stderr, 'waiting for a connection'
                connection, client_address = sock.accept()

                try:
                    print >>sys.stderr, 'connection from', client_address

                    # Receive the data in small chunks and retransmit it
                    buf = StringIO()
                    while True:
                        data = connection.recv(1024)
                        buf.write(data)

                        if len(data)>0:
                            break

                    res = handle_request(json.loads(buf.getvalue()))
                    if len(res)>0:
                        connection.sendall(res)

                finally:
                    # Clean up the connection
                    connection.close()
                    # sock.shutdown(1)
                    # sock.close()

    finally:
        # Cleanup sockets
        print "Closing socket .. "
        # sock.shutdown(1)
        # sock.close()
