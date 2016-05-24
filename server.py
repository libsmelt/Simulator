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
    hybrid_cluster = False
    machine = None
    overlay = None
    group = []
    multimessage = False
    reverserecv = False


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
    overlay = r[u'topology'].split('-')

    overlay_name = overlay[0]
    overlay_args = overlay[1:]

    if overlay_name == 'hybrid':
	overlay_name = 'cluster'
	config.hybrid = True;
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

    print 'Responding with >>>'
    print json.dumps(res)
    print '<<<'

    write_statistics(c.machine)

    return json.dumps(res)


STAT_FILE = 'statistics.json'
def write_statistics(machine):

    # Read
    try:
        with open(STAT_FILE, 'r') as f:
            stat = json.loads(f.read())
            f.close()
    except Exception:
        stat = {}
        raise

    # Update
    stat['num_served'] = stat.get('num_served', 0) + 1
    stat['num_served_%s' % machine] = stat.get('num_served_%s' % machine, 0) + 1


    # Write
    f = open(STAT_FILE, 'w')
    json.dump(stat, f)


def server_loop():
    print 'Starting server'

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('', PORT) # empty string = accept from all addresses
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
