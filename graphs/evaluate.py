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
node_state = []
last_node = -1

class NodeState(object):
    """
    Store node state for evaluation
    """
    def __init__(self):
        self.seq_no = 0

class Result():
    """
    Store result of evaluation
    """
    def __init__(self, time, last_node):
        self.time = time
        self.last_node = last_node


def evalute(topo, root, m, sched):
    """
    Evaluate the latency of sending an individual message along the tree
    @param tree: Overlay as determined by simulator
    @param m: Model representing machine
    @param sched: Scheduler for sending messages
    """
    global round
    global node_queues
    global model
    global node_state
    global schedule
    global last_node

    tree = topo.get_broadcast_tree()
    model = tree
    schedule = sched
    round = 0

    node_state = [NodeState()]*len(model)

    # Construct visualization instance
    global visu
    visu = draw.Output(("visu_%s_%s.tex" % (m.get_name(), topo.get_name())), 
                       m, topo)
    
    send(root, round, [])

    while not terminate():
        consume_event()

    # XXX dirty hack: receive of last node is missing
    # as our nodes are homogeneous, we just add the receive time of the root
    r = Result((round + receive_cost(root)), last_node)
    m.set_evaluation_result(r)
    return r

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
    global last_node
    last_node = dest
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

def send(src, cost, omit):
    """
    Simulate sending a message from given node.
    No message will be send towards nodes given in omit
    """
    assert isinstance(omit, list)
    assert src<len(model)
    send_time = cost
    nb = []
    # For rings: sequence number
    if isinstance(node_state[src], NodeState) and node_state[src].seq_no > 0:
        print "Node %d Received message that was send before, aborting!" % src
        return
    node_state[src] = NodeState()
    node_state[src].seq_no = 1
    # Get a list of neighbors from the scheduler
    nb = schedule.find_schedule(src)
    # # Create list of children first, and the cost of the message list
    # for dest in model.neighbors(src):
    #     if not dest in omit:
    #         nb.append((model.edge_weight((src, dest)), dest))
    # # Find longest path for all neighbors
    # if config.SCHEDULING_SORT_LONGEST_PATH:
    #     nb = get_longest_path(src, omit)
    #     for (nbc, nbn) in nb:
    #         print "longest path from node %d via %d is %d\n" % (src, nbn, nbc)
    # # Sort this list
    # if config.SCHEDULING_SORT or config.SCHEDULING_SORT_LONGEST_PATH:
    #     nb.sort(key=lambda tup: tup[0], reverse=True)
    # # Sort this list
    # if config.SCHEDULING_SORT_ID:
    #     nb.sort(key=lambda tup: tup[1], reverse=False) # Sort by node ID
    # # Walk the list and send messages
    for (cost, dest) in nb:
        if not dest in omit:
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

