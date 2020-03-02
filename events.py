#!/usr/bin/env python3
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
class Event():
    "Empty base object"
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
    def __lt__(self, other) :
        return False

class Send(Event):
    """
    Represents a send operation. When dequeued, a node is ready to
    send a message (i.e. the node is active and idle)
    """

    def get_type(self):
        return 'Send'
    def __lt__(self, other) :
        return True

class Receive(Event):
    """
    Represents a receive operation. When dequeued, a message is
    received from the wire and the receiving node can start receiving
    the message.
    """
    def get_type(self):
        return 'Receive'
    def __lt__(self, other) :
        return True

class Propagate(Event):
    """
    Represent propagation of event. This is enqueued from send(). When
    dequeued, it means that the message has been sent from the sender
    and started to propagate.
    """
    def get_type(self):
        return 'Propagate'
    def __lt__(self, other) :
        return False

class Receiving(Event):
    """Indicates that a node is currently receiving a message and no other
    event is scheduled afterward.

    We need to distinguish between a node that is idle doing nothing and
    a node that is currently receiving, but does not have a send
    operation scheduled.

    This is in case another receive operation for the same core is
    added, to make sure the receive operations do not overlap.

    """
    def get_type(self):
        return 'Receiving'
    def __lt__(self, other) :
        return False
