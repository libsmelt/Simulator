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

class Receive(Event):
    """
    Represents a receive operation. When dequeued, a message is
    received from the wire and the receiving node can start receiving
    the message.
    """

class Propagate(Event):
    """
    Represent propagation of event. This is enqueued from send(). When
    dequeued, it means that the message has been sent from the sender
    and started to propagate.
    """
