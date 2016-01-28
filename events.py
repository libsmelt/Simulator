class Event():
    "Empty base object"
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

class Send(Event):
    """
    Represents a send operation. When dequeued, a node is ready to
    send a message (i.e. the node is active and idle)
    """

    def get_type(self):
        return 'Send'

class Receive(Event):
    """
    Represents a receive operation. When dequeued, a message is
    received from the wire and the receiving node can start receiving
    the message.
    """
    def get_type(self):
        return 'Receive'

class Propagate(Event):
    """
    Represent propagation of event. This is enqueued from send(). When
    dequeued, it means that the message has been sent from the sender
    and started to propagate.
    """
    def get_type(self):
        return 'Propagate'

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
