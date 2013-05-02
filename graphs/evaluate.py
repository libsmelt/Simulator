import events
import heapq
import draw
import config
import pdb

# Evaluation is round-based

# Assumptions:
# 1) nodes never have to process different events at the same time

# XXX It would probably better to have a directed graph!

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

    # Construct visualization instance
    global visu
    visu = draw.Output("visu.tex", len(model))
    
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
    visu.receive(dest, src, round, receive_cost(dest))
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

def _get_longest_path_for_node(node, omit, depth):
    """
    Return the length of the longest path starting at the given node
    Note: Graph must not have cycles (is this true?)
    """
    assert not omit == None
    l = 0
    for n in model.neighbors(node):
        if not n in omit: 
            o_ = omit
            o_.append(node)
            ltmp = model.edge_weight((node, n)) + \
                _get_longest_path_for_node(n, o_, depth+1)
            indent = ''
            for i in range(depth):
                indent += ' '
            print "%sPath length from %d via %d is %d" % (indent, node, n, ltmp)
            l = max(l, ltmp)
    return l

def get_longest_path(src, omit):
    """
    Return the maximum length for subtrees starting at every node
    given in nblist
    """
    paths = []

    assert not omit == None
    omit.append(src)

    print "=================================================="
    for n in model.neighbors(src):
        if not n in omit:
            m = model.edge_weight((src, n)) + \
                _get_longest_path_for_node(n, omit, 0)
            paths.append((m, n))
    return paths

def send(src, cost, omit):
    """
    Simulate sending a message from given node.
    No message will be send towards nodes given in omit
    """
    assert isinstance(omit, list)
    send_time = cost
    nb = []
    # Create list of children first, and the cost of the message list
    for dest in model.neighbors(src):
        if not dest in omit:
            nb.append((model.edge_weight((src, dest)), dest))
    # Find longest path for all neighbors
    if config.SCHEDULING_SORT_LONGEST_PATH:
        nb = get_longest_path(src, omit)
        for (nbc, nbn) in nb:
            print "longest path from node %d via %d is %d\n" % (src, nbn, nbc)
    # Sort this list
    if config.SCHEDULING_SORT or config.SCHEDULING_SORT_LONGEST_PATH:
        nb.sort(key=lambda tup: tup[0], reverse=True)
    # Walk the list and send messages
    for (cost, dest) in nb:
            visu.send(src, dest, send_time, send_cost(src))
            send_time += send_cost(src)
            heapq.heappush(\
                event_queue, \
                    (send_time, events.Propagate(src, dest)))

def terminate():
    """
    Return whether evaluation is termiated
    """
    return len(event_queue)==0

