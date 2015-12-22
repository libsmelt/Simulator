import events
import heapq
import draw
import config
import pdb
import logging
import sched_adaptive

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
        self.seq_no = 0

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

    def __init__(self):
        """
        Reset state

        """
        self.sim_round = 0
        self.event_queue = []
        self.topology = {}
        # Some topologies require state (e.g. rings). We store this state
        # in a list of node states (sequence number for rings)
        self.node_state = {}
        self.last_node = -1
        # Keep track of which nodes are active
        # Lists of nodes that: 
        #  -> received the message already (nodes_active)
        #  -> did _not_ yet receive the message (nodes_inactive)
        self.nodes_active = []
        self.nodes_inactive = []

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

        # Construct visualization instance
        visu_name = ("visu/visu_%s_%s_send_events.tex" % 
                     (m.get_name(), topo.get_name()))
        self.visu = draw.Output(visu_name, m, topo)

        # Evaluate cost starting at _root_
        self.nodes_active.append(root)
        heapq.heappush(self.event_queue, (self.sim_round, events.Send(root, None)))

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
        """
        Consume event from event queue. This will increase the round
        counter

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
        """
        Process propagation event. This will queue a receive event on the
        receiving side

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

        # For rings: sequence number
        # Abort in case the message was seen before
        if dest in self.node_state and \
                isinstance(self.node_state[dest], NodeState) and \
                self.node_state[dest].seq_no > 0:
            print "Node %s Received message that was send before, aborting!" % dest
            return
        self.node_state[dest] = NodeState()
        self.node_state[dest].seq_no = 1

        recv_cmpl = self.sim_round + cost
        heapq.heappush(self.event_queue, (recv_cmpl, events.Send(dest, None)))

    def send(self, src):
        """
        Simulate sending a message from given node. No message will be
        send towards nodes given in omit

        """
        send_time = self.sim_round
        if not src in self.topology.nodes():
            import pdb
            pdb.set_trace()
        assert src in self.topology.nodes()
        nb = []

        # Get a list of neighbors from the scheduler
        nb = self.schedule.find_schedule(src, self.nodes_active)
        assert isinstance(nb, list)
        assert isinstance(self.nodes_active, list)

        # Ignore all nodes that received the message already
        nb_filtered = [ tmp for (cost, tmp) in nb if tmp not in self.nodes_active ]

        # # Sanity checks for adaptive scheduling
        # if isinstance(self.schedule, sched_adaptive.SchedAdaptive):
        #     # Otherwise, state in Scheduler is inconsistent with state of evaluation
        #     # Currently, this state is only the list of active nodes
        #     assert len(nb_filtered) == len(nb) or pdb.set_trace()

        if len(nb_filtered) > 0:
            dest = nb_filtered[0]
            cost = self.model.get_send_cost(src, dest)

            # Adaptive models: need to add edge
            if not self.topology.has_edge((src,dest)):
                self.topology.add_edge(
                    (src, dest),
                    self.model.graph.edge_weight((src, dest)))

            self.visu.send(src, dest, send_time, cost)
            print 'Send(%d,%s,%s) - cost %d' % \
                (self.sim_round, str(src), str(dest), cost)

            send_compl = send_time + cost

            # Add propagation event to the heap to signal to propagate
            # the message after the send operation completes
            heapq.heappush(\
                self.event_queue, \
                    (send_compl, events.Propagate(src, dest)))

            # Add send event to signal that further messages can be
            # sent once the current message completed the current send
            # operation.
            heapq.heappush(\
                self.event_queue, \
                    (send_compl, events.Send(src, None)))

            # receiver becomes active
            self.nodes_active.append(dest)

    def terminate(self):
        """
        Return whether evaluation is termiated
        """
        return len(self.event_queue)==0
