import events
import heapq
import draw
import config
import pdb
import logging
import sched_adaptive
import copy # for heapq


# We assume that the propagation time is zero. The cost for
# transporting messages is captured in t_send and t_receive.
T_PROPAGATE = 0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
        
    def receive_handler(self, eval_context, core, from_core, time):
        """Triggered when a message was received on <core>

        """
        return True

    def is_terminated(self, eval_context):
        """Indicate if the protocol is terminated

        Normally, this can be determined by the execution process
        directly. Otherwise, it can be configured here

        """
        return True
        

class AB(Protocol):
    """Atomic broadcast protocol
    """
    def __init__(self):
        # Keep track of which nodes are active
        # Lists of nodes that: 
        #  -> received the message already (cores_active)
        self.cores_active = []

    def get_name(self):
        return 'atomic broadcast'
    
    def set_initial_state(self, eval_context, root):
        """Evaluate cost starting at root of overlay
        """
        eval_context.schedule_node(root)
        self.cores_active = [root]
        
    
    def idle_handler(self, eval_context, core, time):
        """Idle nodes in the atomic broadcast will send messages to nodes that
        have not yet seen the message.

        The scheduler decides where messages should be sent.

        """
        
        # Get a list of neighbors from the scheduler
        nb = eval_context.schedule.find_schedule(core, self.cores_active)
        assert isinstance(nb, list)
        assert isinstance(self.cores_active, list)

        # Ignore all nodes that received the message already
        nb_filtered = [ tmp for (cost, tmp) in nb if tmp not in self.cores_active ]

        if len(nb_filtered) > 0:
            dest = nb_filtered[0]
            cost = eval_context.get_send_cost(core, dest)

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
            self.cores_active.append(dest)
            
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
    

    def __init__(self):
        
        # A dictionary, storing for each node how many messages have been received
        self.num_msgs = {}
        self.parents = {}
        self.root = None

    
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


    def receive_handler(self, eval_context, core, from_core, time):

        self.num_msgs[core] = self.num_msgs.get(core, 0) + 1
        num = self.num_msgs[core]

        num_children = len([ x for (x, p) in self.parents.items() if p == int(core) ])

        print bcolors.OKBLUE + \
            ('%d: Core %d receiving message %d/%d' %
             (time, core, num, num_children)) + \
            bcolors.ENDC

        assert num<=num_children
        return num>=num_children
        
    
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

            send_compl = time + eval_context.get_send_cost(core, parent)
            
            # Note: don't have to enqueue the same core as sender again
            eval_context.schedule_node(parent, send_compl, core)

        
class Barrier(Protocol):
    """Represents a barrier

    """

    # Constants
    IDLE = 0
    REDUCE = 1
    BC = 2

    def __init__(self):
        print 'Initializing new Barrier'
        self.state = {}
        self.leaf_nodes = {}
        # Keep track of which nodes are active
        # Lists of nodes that: 
        #  -> received the message already (cores_active)
        self.cores_active = []

        # A dictionary, storing for each node how many messages have been received
        self.num_msgs = {}
        self.parents = {}
        self.num_msgs = {} # For reduce: how many messages have been received
        self.root = None
        self.msg_log = {}
    
    def get_name(self):
        return 'barrier'
    
    def set_initial_state(self, eval_context, root):
        """Barriers start with a reduction, so initially, all leaf nodes are
        active.

        """
        leaf_nodes = eval_context.topo.get_leaf_nodes(eval_context.schedule)
        print 'Leaf nodes are', str(leaf_nodes)

        for l in leaf_nodes:
            self.state[l] = Barrier.REDUCE
            eval_context.schedule_node(l)

        self.parents = eval_context.topo.get_parents(eval_context.schedule)
        print 'Parent relationship: ', self.parents

        self.root = root

        

    def idle_handler(self, eval_context, core, time):
        """
        """
        # Get a list of neighbors from the scheduler
        nb = eval_context.schedule.find_schedule(core, self.cores_active)
        assert isinstance(nb, list)
        assert isinstance(self.cores_active, list)

        # Ignore all nodes that received the message already
        nb_filtered = [ tmp for (cost, tmp) in nb if tmp not in self.cores_active ]

        # --------------------------------------------------
        # Reduce state
        if self.state.get(core, Barrier.IDLE) == Barrier.REDUCE:
            
            print ('Node %d is in reduce state and received a message '
                   'or no neighbors (%d)') % (core, len(nb_filtered))

            # There is nothing to do for the root
            if core == self.root:
                return

            self.num_msgs[core] = self.num_msgs.get(core, 0) + 1
            num = self.num_msgs[core] - 1
            plist = eval_context.topo.get_parents(eval_context.schedule)
            
            num_children = len([ x for (x, p) in plist.items() \
                                 if p == int(core) ])

            # Each core has only one parent - send a message there
            parent = eval_context.topo.get_parents(eval_context.schedule).get(core, None)
            assert parent != None # Unless we are the root, we have a parent
            print 'Count on', core, 'out of', num_children, 'is', num

            if num >= num_children:
                print '%d: Sending to parent %d (%d/%d)' % (core, parent, num, num_children)

                cost = eval_context.get_send_cost(core, parent)
                
                print 'Send(%d,%s,%s) - Barrier - Reduce - NBs=%d - cost %d' % \
                    (eval_context.sim_round, str(core), str(parent), 1, cost)

                send_compl = time + cost

                # Note: don't have to enqueue the same core as sender again
                eval_context.schedule_node(parent, send_compl, core)

        # --------------------------------------------------
        # Broadcast state
        elif len(nb_filtered) > 0:

            assert self.state[core] == Barrier.BC
            print 'Node %d is in broadcast state and received a message ' % core
           
            dest = nb_filtered[0]
            cost = eval_context.get_send_cost(core, dest)

            # Adaptive models: need to add edge
            if not eval_context.topology.has_edge((core,dest)):
                eval_context.topology.add_edge(
                    (core, dest),
                    eval_context.model.graph.edge_weight((core, dest)))

            eval_context.visu.send(core, dest, time, cost)
            print 'Send(%d,%s,%s) - Barrier - BC - NBs=%d - cost %d' % \
                (eval_context.sim_round, str(core), str(dest),
                 len(nb_filtered), cost)

            send_compl = time + cost

            # Make receiver active
            eval_context.schedule_node(dest, send_compl, core)
            self.cores_active.append(dest)
            
            # Add send event to signal that further messages can be
            # sent once the current message completed the current send
            # operation.
            heapq.heappush(\
                eval_context.event_queue, \
                    (send_compl, events.Send(core, None)))


                
    def receive_handler(self, eval_context, core, from_core, time):
        """Triggered when a message was received on <core>

        State diagram.
        """
        print 'Receiving message on core %d' % core

        curr_core_state = self.state.get(core, Barrier.IDLE)

        # Record state for debugging purposes
        self.msg_log[core] = self.msg_log.get(core, []) + [
            (core, from_core, curr_core_state)]
        
        if curr_core_state == Barrier.IDLE:
            # Trigger send unless as soon as we have received a message from
            # all children - compare with Reduction.receive_handler
            self.num_msgs[core] = self.num_msgs.get(core, 0) + 1
            num_children = len([x for (x, p) in self.parents.items() if p == int(core) ])
            assert self.num_msgs[core]<=num_children
            start_bc = (self.num_msgs[core]==num_children)
            
            if start_bc:
                # Change state to REDUCE
                self.state[core] = Barrier.REDUCE

            return start_bc
                    
        elif curr_core_state == Barrier.REDUCE:
            # Change state to BROADCAST, trigger sending a message
            self.state[core] = Barrier.BC
            return True

        elif curr_core_state == Barrier.BC:
            # For the root, where we _manually_ set change the state
            # to BC, it is normal to see this spurious state
            # change. Otherwise, it should not happen.
            if core == self.root:
                return True
                
            assert not "Node is already in Reduces state - how can this happen?"
            
        else:
            raise Exception('Received unexpected message')

        assert not "We could never be here, but return in one of the if-clauses"



    def is_terminated(self, eval_context):
        """Indicate if the protocol is terminated

        The barrier is finished after each node is in .. state
        """

        print 'Checking if Barrier is terminated - %d' % len(self.state)

        reduce_done = True
        finished = True
        for (core, state) in self.state.items():
            if state != Barrier.BC:
                finished = False
            if state != Barrier.REDUCE:
                reduce_done = False

        if reduce_done:
            
            print '------------------------------'
            print 'REDUCE --> BROADCAST (from %d)' % self.root
            print '------------------------------'

            import debug
            
            # Activate BC for root
            self.state[self.root] = Barrier.BC
            
            # Reset state of all cores + schedule root
            eval_context.schedule_node(self.root)
            self.cores_active = [self.root]

            
        return finished

        

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
        self.send_batch = 0 # <<< number of sends in current batch

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

        # Reset send history
        m.reset()
            
        for protocol in [ AB(), Reduction(), Barrier() ]:

            print 'Evaluating protocol %s' % \
                protocol.get_name()
            
            ev = Evaluate(protocol)
            # import cProfile
            # cProfile.run('ev = Evaluate(protocol)')
            # return None
            
            res.append((protocol.get_name(), ev.evaluate(topo, root, m, sched)))

            # Mark the schedule as finished, relevant for the adaptive
            sched.next_eval()
            
            # Reset send history
            m.reset()

        return res 
        
    
    def __init__(self, _protocol):
        """Reset state

        @param _protocol Instance of the the protocol that should be
        evaluated

        """
        self.sim_round = 0
        self.event_queue = []
        self.topology = {}
        
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

        # Initialize per-node state
        for core in self.model.get_cores():
            self.node_state[core] = NodeState()

        # Construct visualization instance
        visu_name = ("visu/visu_%s_%s_%s.tex" % 
                     (m.get_name(), topo.get_name(),
                      self.protocol.get_name().replace(' ', '_')))
        self.visu = draw.Output(visu_name, m, topo)

        # Set initial state
        self.protocol.set_initial_state(self, root)
        
        while not self.terminate():
            self.consume_event()

        # Add cost for communication last_node -> root, since we will
        # evaluate the cost of the protocol in real hardware starting
        # at the last node
        # * Send cost
        final_time = self.sim_round
        r = Result(self.sim_round, self.last_node, visu_name)
        send_feedback = self.model.query_send_cost(self.last_node, root)

        print "Terminating(%d,%s,%s) - cost %d for last_node -> root" % \
            (self.sim_round, str(self.last_node), str(root),
             send_feedback + self.model.get_receive_cost(self.last_node, root))
        self.sim_round += send_feedback
        # * Propagation
        self.sim_round += T_PROPAGATE
        # * Receive cost
        self.sim_round += self.model.get_receive_cost(self.last_node, root);
        r.time = self.sim_round

        # XXX Check if this includes the receive cost on the last node (it should)
        self.model.set_evaluation_result(r)

        self.visu.finalize(int(final_time))

        return r

    def consume_event(self):
        """Consume event from event queue. This will increase the round
        counter.

        There are three types of events:

        - propagate:

        - send: A send should be performed. Triggers calling the
          function send().

        - receive:

        - receiving: This seems to be some kind of DUMMY operation,
          related to the problem of having several receives on the
          same core (e.g. Reduction). In that case, overlapping
          Receive operations have to re-arranged.

        What the fuck is the difference between receive and receiving?

        """
        (p, e) = heapq.heappop(self.event_queue)
        assert(p>=self.sim_round)
        self.sim_round = p

        d = int(e.dest) if e.dest != None else -1
        s = int(e.src) if e.src != None else -1
        
        print bcolors.OKGREEN + \
            ('%d: event %s -- Core %d -> Core %d' %
             (self.sim_round, e.get_type(), s, d)) + \
            bcolors.ENDC
        

        if isinstance(e, events.Propagate):
            self.propagate(e.src, e.dest)

        if isinstance(e, events.Receive):
            self.receive(e.src, e.dest)

        if isinstance(e, events.Send):
            assert e.dest is None
            self.send(e.src)

        if isinstance(e, events.Receiving):
            print 'Receiving done'

    def propagate(self, src, dest):
        """Process propagation event. This will queue a receive event on the
        receiving side

        We don't really have to make this part of the protocol logic,
        since propagation time should be independent of the protocol
        used.

        """

        enqueue_at = self.sim_round
        
        # Check if the receiver is already sending.
        for he in self.event_queue:
            (ts, ev) = he

            if ev.dest == dest:
                print bcolors.BOLD + \
                    ('%d: Core %d propagete, found existing event %s at %d %d -> %d - ' %
                     (self.sim_round, dest, ev.get_type(), ts, ev.src, ev.dest)) + \
                    bcolors.ENDC

                if isinstance(ev, events.Receiving):

                    _new = max(enqueue_at, ts)
                    
                    print bcolors.BOLD + bcolors.FAIL + \
                        ('%d: Core %d is already receiving %d -> %d' %
                         (self.sim_round, dest, enqueue_at, _new)) + bcolors.ENDC

                    assert ts >= enqueue_at
                    enqueue_at = _new
        
        w = T_PROPAGATE
        heapq.heappush(self.event_queue, (enqueue_at + w, events.Receive(src, dest)))

        # Node (src) has just sent a message, increment send batch size
        self.node_state[src].send_batch += 1

        print "Propagate(%d,%s->%s) - cost %d" % (self.sim_round, str(src), str(dest), w)

    def receive(self, src, dest):
        """Receive a message on dest XXX This is a bit of a misnomer. _dest_
        is the node where the message is received. Send will be called to
        trigger sending of messages to children.

        XXX The problem here is that a core cannot concurrently
        receive elements. So in here, we need to check the queue and
        update all other's receive events to at least (self.sim_round + receive_cost)

        """
        assert (dest>=0)
        self.last_node = dest
        
        # Get receive cost
        cost = self.model.get_receive_cost(src, dest)
        self.visu.receive(dest, src, self.sim_round, cost)
        print "Receive(%d,%s->%s) Core %d- cost %d" \
                         % (self.sim_round, str(src), str(dest), dest, cost)

        # Node (src) has just received a mesage, reset send batch
        self.node_state[dest].send_batch = 0
        
        schedule_send = self.protocol.receive_handler( \
            self, dest, src, self.sim_round)

        # It's possible that there is another event scheduled for the
        # receiving node. In that case, we need to update the
        # timestamp accordingly.

        _heap = []
        
        for he in self.event_queue:
            (ts, ev) = he
            
            if ev.dest == dest or ev.src == dest:
                
                print bcolors.WARNING + \
                    ('%d: Core %d found another event %s at %d %d -> %d - ' %
                     (self.sim_round, dest, ev.get_type(), ts, ev.src, ev.dest)) + \
                    bcolors.ENDC

            if ev.dest == dest and isinstance(ev, events.Receive):

                assert (ev.src != src) # this should be from a different source
                
                print bcolors.WARNING + \
                    ('%d: Core %d found another event %s at %d from %d - '
                     'cost: %d - new ts %d' %
                     (self.sim_round, dest, ev.get_type(), ts, ev.src,
                      cost, ts + cost)) + \
                    bcolors.ENDC
                # assert (ts>=self.sim_round) # otherwise, we'd have an
                #                             # event on the queue that
                #                             # should have been
                #                             # executed BEFORE the
                #                             # current time.
                # active_event = max(active_event, ts)
                _heap.append((ts + cost, ev))
                
            else:
                _heap.append(he)

        self.event_queue = _heap
        heapq.heapify(self.event_queue)

        print [ (ts, ev.src) for (ts, ev) in self.event_queue if \
                ev.dest == dest and isinstance(ev, events.Receive) ]

        # Schedule a send? after the receive is complete
        if schedule_send:
            
            recv_cmpl = self.sim_round + cost
            print bcolors.OKGREEN + \
                ('%d: Core %d is scheduling a send operation %d at %d' %
                 (self.sim_round, dest, src, recv_cmpl)) + \
                 bcolors.ENDC

            heapq.heappush(self.event_queue, (recv_cmpl, events.Send(dest, None)))

        else:

            recv_cmpl = self.sim_round + cost
            print bcolors.OKGREEN + \
                ('%d: Core %d is scheduling a DUMMY operation %d at %d' %
                 (self.sim_round, dest, src, recv_cmpl)) + \
                 bcolors.ENDC

            heapq.heappush(self.event_queue, (recv_cmpl, events.Receiving(src, dest)))
            

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
        return len(self.event_queue)==0 and self.protocol.is_terminated(self)


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


    def get_send_cost(self, sender, receiver):

        _batchsize = self.node_state[sender].send_batch + 1

        import model
        assert isinstance (self.model, model.Model)

        cost = self.model.get_send_cost(sender, receiver, batchsize=_batchsize)
        
        logging.info(('Send: Getting send cost %d->%d for batchsize %d = %d' % \
            (sender, receiver, _batchsize, cost)))
                     
        return cost
