import events
import heapq
import draw
import config
import pdb

# Evaluation is event based. We realize this using a priority heap
# with the time at which the event is happening as priority and pop
# the top of this queue in every step.

# Assumptions:
# 1) nodes never have to process different events at the same time

# XXX It would probably better to have a directed graph!

round = 0
event_queue = []
model = {}
# Some topologies require state (e.g. rings). We store this state
# in a list of node states (sequence number for rings)
node_state = []
last_node = -1
# Keep track of which nodes are active
# * lists of nodes that: 
#  -> received the message already (nodes_active)
#  -> did _not_ yet receive the message (nodes_inactive)
nodes_active = []
nodes_inactive = []

# ==================================================
class NodeState(object):
    """
    Store node state for evaluation
    """
    def __init__(self):
        self.seq_no = 0

# ==================================================
class Result():
    """
    Store result of evaluation
    """
    def __init__(self, time, last_node):
        self.time = time
        self.last_node = last_node

# ==================================================
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
    visu = draw.Output(("visu_%s_%s_send_events.tex" % \
                        (m.get_name(), topo.get_name())), 
                       m, topo)

    nodes_active.append(root)
    heapq.heappush(event_queue, (round, events.Send(root, None)))

    while not terminate():
        consume_event()

    # XXX dirty hack: receive of last node is missing
    # as our nodes are homogeneous, we just add the receive time of the root
    r = Result((round + receive_cost(root)), last_node)
    
    m.set_evaluation_result(r)

    visu.finalize()

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

    if isinstance(e, events.Send):
        assert e.dest is None
        send(e.src)

def propagate(src, dest):
    """
    Process propagation event.
    This will queue a receive event on the receiving side
    """
    w = model.edge_weight((src, dest))
    heapq.heappush(event_queue, (round + w, events.Receive(src, dest)))

def receive(src, dest):
    """
    Receive a message on dest XXX This is a bit of a misnomer. _dest_
    is the node where the message is received. Send will be called to
    trigger sending of messages to children.
    """
    print "{%d}: receiving message from {%d} in round %d" \
        % (dest, src, round)
    global last_node
    last_node = dest
    visu.receive(dest, src, round, receive_cost(dest))

    # For rings: sequence number
    # Abort in case the message was seen before
    if isinstance(node_state[dest], NodeState) and node_state[dest].seq_no > 0:
        print "Node %d Received message that was send before, aborting!" % dest
        return
    node_state[dest] = NodeState()
    node_state[dest].seq_no = 1

    recv_cmpl = round + receive_cost(dest)
    heapq.heappush(event_queue, (recv_cmpl, events.Send(dest, None)))

def send_cost(node):
    """
    Return send cost. This is constant for the time being as we
    evaluate heterogeneous machines only.
    XXX read from model
    """
    return 10

def receive_cost(node):
    """
    Return send cost. This is constant for the time being as we
    evaluate heterogeneous machines only.
    XXX read from model
    """
    return 10

def send(src):
    """
    Simulate sending a message from given node.
    No message will be send towards nodes given in omit
    """
    send_time = round
    assert src<len(model)
    nb = []

    # Get a list of neighbors from the scheduler
    nb = schedule.find_schedule(src)
    # Walk the list and send messages

    # XXX Very dirty way of removing every element of <nodes_active>
    # from <nb> -> fix
    nb_filtered = []
    for (cost, tmp) in nb:
        if tmp not in nodes_active:
            nb_filtered.append(tmp)

    if len(nb_filtered) > 0:
        dest = nb_filtered[0]
        visu.send(src, dest, send_time, send_cost(src))
        send_compl = send_time + send_cost(src)
        # Add propagation event to the heap to signal to propagate
        #  the message after the send operation completes
        heapq.heappush(\
            event_queue, \
                (send_compl, events.Propagate(src, dest)))
        # Add send event to signal that further messages can be
        # sent once the current message completed the current send
        # operation.
        heapq.heappush(\
            event_queue, \
                (send_compl, events.Send(src, None)))

        # receiver becomes active
        nodes_active.append(dest)


def terminate():
    """
    Return whether evaluation is termiated
    """
    return len(event_queue)==0

