import events
import heapq

# Evaluation is round-based

# Assumptions:
# 1) nodes never have to process different events at the same time

round = 0
event_queue = []
model = {}

def evalute(tree, root):
    """
    Evaluate the latency of sending an individual message along the tree
    """
    global round
    global node_queues
    global model

    model = tree
    
    send(root, round, [])

    while not terminate():
        consume_event()

    # XXX dirty hack: receive of last node is missing
    # as our nodes are homogeneous, we just add the receive time of the root
    return round + receive_cost(root)

def consume_event():
    """
    Consume event from event queue
    This will increase the round counter
    """
    global round
    (p, e) = heapq.heappop(event_queue)
    assert(p>=round)
    round = p

    if isinstance(e, events.Propagate):
        propagate(e.src, e.dest)

    if isinstance(e, events.Receive):
        receive(e.src, e.dest)

def propagate(src, dest):
    """
    Process propagation event.
    This will queue a receive event on the receiving side
    """
    w = model.edge_weight((src, dest))
    heapq.heappush(event_queue, (round + w, events.Receive(src, dest)))

def receive(src, dest):
    """
    Receive a message on dest
    Send will be called to trigger sending of messages to children
    """
    print "{%d}: receiving message from {%d} in round %d" \
        % (dest, src, round)
    send(dest, round+receive_cost(dest), [src])

def send_cost(node):
    """
    Return send cost. This is constant for the time being as we
    evaluate heterogeneous machines only.
    """
    return 10

def receive_cost(node):
    """
    Return send cost. This is constant for the time being as we
    evaluate heterogeneous machines only.
    """
    return 10

def send(src, cost, omit):
    """
    Simulate sending a message from given node.
    No message will be send towards nodes given in omit
    XXX Scheduling decision here
    """
    for n in model.neighbors(src):
        if not n in omit:
            cost+=send_cost(src)
            heapq.heappush(event_queue, \
                               (cost, events.Propagate(src, n)))

def terminate():
    """
    Return whether evaluation is termiated
    """
    return len(event_queue)==0

