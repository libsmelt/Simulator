import events
import heapq
import draw
import config
import pdb
import logging
import sched_adaptive


class Protocol(object):
    """Represent a protocol that is executed  by the Simulator
    """

    def set_initial_state(self, eval_context, root):
        """Initialize protocol execution

        @param eval_context A reference to the evaluate instance
        executing the Simulation.

        @param root The root node of the topology
        """

    def idle_handler(self, eval_context, core, time):
        """Executed  when a core because idle

        @param eval_context A reference to the evaluate instance
        executing the Simulation.

        @param core The core that has become idel

        @param time The current time
        """

    def get_name(self):
        """Representative name for the protocol
        """
        

class AB(Protocol):
    """Atomic broadcast protocol
    """
    
    # Keep track of which nodes are active
    # Lists of nodes that: 
    #  -> received the message already (nodes_active)
    nodes_active = []

    def get_name(self):
        return 'atomic broadcast'
    
    def set_initial_state(self, eval_context, root):
        """Evaluate cost starting at root of overlay
        """
        eval_context.schedule_node(root)
        self.nodes_active = [root]
        
    
    def idle_handler(self, eval_context, core, time):
        """Idle nodes in the atomic broadcast will send messages to nodes that
        have not yet seen the message.

        The scheduler decides where messages should be sent.

        """
        
        # Get a list of neighbors from the scheduler
        nb = eval_context.schedule.find_schedule(core, self.nodes_active)
        assert isinstance(nb, list)
        assert isinstance(self.nodes_active, list)

        # Ignore all nodes that received the message already
        nb_filtered = [ tmp for (cost, tmp) in nb if tmp not in self.nodes_active ]

        if len(nb_filtered) > 0:
            dest = nb_filtered[0]
            cost = eval_context.model.get_send_cost(core, dest)

            # Adaptive models: need to add edge
            if not eval_context.topology.has_edge((core,dest)):
                eval_context.topology.add_edge(
                    (core, dest),
                    eval_context.model.graph.edge_weight((core, dest)))

            eval_context.visu.send(core, dest, time, cost)
            print 'Send(%d,%s,%s) - cost %d' % \
                (eval_context.sim_round, str(core), str(dest), cost)

            send_compl = time + cost

            # Make receiver active
            eval_context.schedule_node(dest, send_compl, core)
            self.nodes_active.append(dest)
            
            # Add send event to signal that further messages can be
            # sent once the current message completed the current send
            # operation.
            heapq.heappush(\
                eval_context.event_queue, \
                    (send_compl, events.Send(core, None)))


class Reduction(Protocol):
    """Atomic broadcast protocol
    """

    def get_name(self):
        return 'reduction'
    
    # A dictionary, storing for each node how many messages have been received
    num_msgs = {}
    parents = {}
    root = None
    
    def set_initial_state(self, eval_context, root):
        """Evaluate cost starting at root of overlay
        """
        leaf_nodes = eval_context.topo.get_leaf_nodes(eval_context.schedule)
        print 'Leaf nodes are', str(leaf_nodes)

        for l in leaf_nodes:
            eval_context.schedule_node(l)

        self.parents = eval_context.topo.get_parents(eval_context.schedule)
        print 'Parent relationship: ', self.parents

        self.root = root
        
    
    def idle_handler(self, eval_context, core, time):
        """Idle nodes in the atomic broadcast will send messages to nodes that
        have not yet seen the message.

        The scheduler decides where messages should be sent.

        This function will be called for nodes that are idle, but
        active.

        """

        # There is nothing to do for the root
        if core == self.root:
            return
        
        self.num_msgs[core] = self.num_msgs.get(core, 0) + 1
        num = self.num_msgs[core]

        num_children = len([ x for (x, p) in self.parents.items() if p == int(core) ])
        
        # Each core has only one parent - send a message there
        parent = self.parents.get(core, None)
        assert parent != None # Unless we are the root, we have a parent
        print 'Count on', core, 'out of', num_children, 'is', num

        if num >= num_children:
            print 'Sending to parent', parent

            send_compl = time + eval_context.model.get_send_cost(core, parent)
            
            # Note: don't have to enqueue the same core as sender again
            eval_context.schedule_node(parent, send_compl, core)

        
        
        

# Evaluation is event based. We realize this using a priority heap
# with the time at which the event is happening as priority and pop
# the top of this queue in every step.

# Assumptions:
# 1) nodes never have to process different events at the same time

# XXX It would probably better to have a directed graph!

# ==================================================
class NodeState(object):
    """
    Store node state for evaluation

    """
    def __init__(self):
        self.nth = None

# ==================================================
class Result():
    """
    Store result of evaluation

    """
    def __init__(self, time, last_node, visu_name):
        # Time _not_ including last_node -> root, i.e. to allow everyone sending
        self.time_no_ab = time
        # Time including sender -> root
        self.time = None 
        self.last_node = last_node
        self.visu_name = visu_name

# ==================================================
class Evaluate():
    """Simulates a given algorithm on a given machine

    This class manages the event queue, which is used to trigger send
    and receive operations. It also manages per-node state.

    """

    @staticmethod
    def evaluate_all(topo, root, m, sched):
        """Evaluate all protocols

        """
        res = []

        for protocol in [ AB(), Reduction() ]:
            
            ev = Evaluate(protocol)
            res.append((protocol.get_name(), ev.evaluate(topo, root, m, sched)))

        return res 
        
    
    def __init__(self, _protocol):
        """Reset state

        @param _protocol Instance of the the protocol that should be
        evaluated

        """
        self.sim_round = 0
        self.event_queue = []
        self.topology = {}
        
        # Some topologies require state (e.g. rings). We store this state
        # in a list of node states (sequence number for rings)
        self.node_state = {}
        self.last_node = -1
        
        #
        # The protocol that should be simulated
        self.protocol = _protocol
        

    def evaluate(self, topo, root, m, sched):
        """
        Evaluate the latency of sending an individual message along the tree

        @param topo: (class: overlay.Overlay) Overlay as determined by simulator
        @param m: Model representing machine
        @param sched: Scheduler for sending messages

        """
        import hybrid_model
        import overlay

        assert isinstance(topo, overlay.Overlay)
        print 'Evaluate overlay', str(topo), 'using scheduler', str(sched), \
            'tree is', str(topo.get_tree())

        assert len(topo.get_tree())==1 # Don't support evaluation for Hybrid models yet
        for l in topo.get_tree():
            if isinstance(l, hybrid_model.MPTree):
                assert not self.topology # We only support one Overlay currently
                self.topology = l.graph

        self.schedule = sched
        self.model = m
        self.sim_round = 0
        self.topo = topo

        # Construct visualization instance
        visu_name = ("visu/visu_%s_%s_send_events.tex" % 
                     (m.get_name(), topo.get_name()))
        self.visu = draw.Output(visu_name, m, topo)

        # Set initial state
        self.protocol.set_initial_state(self, root)
        
        while not self.terminate():
            self.consume_event()

        # Add cost for communication last_node -> root, since we will
        # evaluate the cost of the protocol in real hardware starting
        # at the last node
        # * Send cost
        r = Result(self.sim_round, self.last_node, visu_name)
        print "Terminating(%d,%s,%s) - cost %d for last_node -> root" % \
            (self.sim_round, str(self.last_node), str(root), 
             self.model.get_send_cost(self.last_node, root) + 
             self.topology.edge_weight((self.last_node, root)) +
             self.model.get_receive_cost(self.last_node, root))
        self.sim_round += self.model.get_send_cost(self.last_node, root);
        # * Propagation
        self.sim_round += self.topology.edge_weight((self.last_node, root))
        # * Receive cost
        self.sim_round += self.model.get_receive_cost(self.last_node, root);
        r.time = self.sim_round

        # XXX Check if this includes the receive cost on the last node (it should)
        self.model.set_evaluation_result(r)

        self.visu.finalize()

        return r

    def consume_event(self):
        """Consume event from event queue. This will increase the round
        counter.

        There are three types of events:

        - propagate:

        - send: A send should be performed. Triggers calling the
          function send().

        - receive:

        """
        (p, e) = heapq.heappop(self.event_queue)
        assert(p>=self.sim_round)
        self.sim_round = p

        if isinstance(e, events.Propagate):
            self.propagate(e.src, e.dest)

        if isinstance(e, events.Receive):
            self.receive(e.src, e.dest)

        if isinstance(e, events.Send):
            assert e.dest is None
            self.send(e.src)

    def propagate(self, src, dest):
        """Process propagation event. This will queue a receive event on the
        receiving side

        We don't really have to make this part of the protocol logic,
        since propagation time should be independent of the protocol
        used.

        """
        w = self.topology.edge_weight((src, dest))
        heapq.heappush(self.event_queue, (self.sim_round + w, events.Receive(src, dest)))
        print "Propagate(%d,%s,%s) - cost %d" % (self.sim_round, str(src), str(dest), w)

    def receive(self, src, dest):
        """
        Receive a message on dest XXX This is a bit of a misnomer. _dest_
        is the node where the message is received. Send will be called to
        trigger sending of messages to children.
        """
        self.last_node = dest
        cost = self.model.get_receive_cost(src, dest)
        self.visu.receive(dest, src, self.sim_round, cost)
        print "Receive(%d,%s,%s) - cost %d" \
                         % (self.sim_round, str(dest), str(src), cost)

        recv_cmpl = self.sim_round + cost
        heapq.heappush(self.event_queue, (recv_cmpl, events.Send(dest, None)))

    def send(self, src):
        """
        Simulate sending a message from given node. No message will be
        send towards nodes given in omit

        """
        assert src in self.topology.nodes()
        self.protocol.idle_handler(self, src, self.sim_round)

        
    def terminate(self):
        """
        Return whether evaluation is termiated
        """
        return len(self.event_queue)==0


    def schedule_node(self, node, time=None, sender=-1):
        """Make node activate and schedule send event

        This can either be after receiving a message from some other
        node, in which case the sender node and time when the message
        will be sent (and on the "wire") have to be given as argument.

        Otherwise, the node is set active without registering a parent
        node and without simulating a propagation event. This is
        useful to setup the inital state of the initialization
        (i.e. some nodes should start already in active state,
        e.g. the root in a broadcast)

        """
        if not time:
            time = self.sim_round

        if sender>=0:
            # Node is activated after receiving node from <sender>
            # -> propagate message first
            ev = events.Propagate(sender, node)
        else:
            # Node is activated initialy
            # -> register send directly
            ev = events.Send(node, None)

        logging.info('activate_node %d, generating event %s' % (node, str(ev)))
        
        heapq.heappush(self.event_queue, (time, ev))

