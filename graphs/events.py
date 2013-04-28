class Event():
    "Empty base object"
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

class Send(Event):
    "Represents a send operation"

class Receive(Event):
    "Represents a receive operation"

class Propagate(Event):
    "Represent propagation of event"
