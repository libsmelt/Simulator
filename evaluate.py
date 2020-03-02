#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
import events
import heapq
import draw
import logging

# We assume that the propagation time is zero. The cost for
# transporting messages is captured in t_send and t_receive.
T_PROPAGATE = 0

assert T_PROPAGATE == 0 # Otherwise sched_adaptive's
                        # optimize_scheduling needs an update

from helpers import bcolors

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

    def send_last_node(self):
        """Should a message be sent from the last node.

        """
        return False


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

    def send_last_node(self):
        return True

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
        nb_filtered = [ tmp for (_, tmp) in nb if tmp not in self.cores_active ]

        if len(nb_filtered) > 0:

            # --------------------------------------------------
            # Send a message
            # --------------------------------------------------

            # Select the node to send to
            dest = nb_filtered[0]

            # Determine the cost of the send operation. This is needed
            # for two reasons:
            #
            # - visualization: the size of the send box to be drawn
            # - event scheduling: when is the node free again after sending
            _cost_real = eval_context.model.get_send_cost(core, dest, False, False)
            cost = eval_context.model.get_send_cost(core, dest, True, True)
            cost_real = max(_cost_real, cost)

            logging.info(('Correcting cost %2d %2d cost %7.2f %7.2f -> %7.2f' %\
                              (core, dest, cost, _cost_real, cost_real)))

            # Adaptive models: need to add edge
            if not eval_context.topology.has_edge((core,dest)):
                eval_context.topology.add_edge(
                    (core, dest),
                    eval_context.model.graph.edge_weight((core, dest)))

            eval_context.visu.send(core, dest, time, cost)
            logging.info(('% 5d   Send(%s,%s) - cost % 4d   done=% 5d' % \
                (eval_context.sim_round, str(core), str(dest), cost,
                 cost+eval_context.sim_round)))

            # Calculate when node is free again
            send_compl = time + cost
            send_compl_real = time + cost_real

            # Make receiver active
            eval_context.schedule_node(dest, send_compl_real, core)
            self.cores_active.append(dest)

            # Add send event to signal that further messages can be
            # sent once the current message completed the current send
            # operation.
            heapq.heappush(\
                eval_context.event_queue, \
                    (send_compl, events.Send(core, None)))



    def receive_handler(self, eval_context, core, from_core, time):
        """Triggered when a message was received on <core>

        """
        time += eval_context.model.get_receive_cost(from_core, core)

        return True

    def draw(self, e):

        e.schedule.visualize(e.model, e.topo)

    def is_terminated(self, eval_context):
        """Protocol is terminated, output core timing

        We can now try to optimize the tree if either "shuffle" or
        "sort" is given as an option for the topology.

        """

        self.draw(eval_context)
        num_reorders = 0

        # --------------------------------------------------
        # Step 2:
        # --------------------------------------------------

        logging.info(('--------------------------------------------------'))
        logging.info(('-- TERMINATED evaluation'))
        logging.info(('--------------------------------------------------'))

        # First, ensure that the send histories match
        eval_context.schedule.assert_history()

        if not eval_context.topo.options.get('shuffle', False):
            return True

        # We reshuffle until as long as we still optimize the tree
        optimize = True

        while optimize:

            # Determine the old slack
            # --------------------------------------------------
            c_idle, c_activated = eval_context.schedule.simulate_current()
            cost_tree = eval_context.schedule.cost_tree()

            # Reorder tree FIRST
            # --------------------------------------------------
            # Since we reorder the tree first, we have to update our
            # slack-window, i.e. the first idle and last terminated
            # cores.
            if eval_context.topo.options.get('sort', False):

                # ------------------------------
                # Update schedule
                # ------------------------------
                # Optimize schedule and return new idel and activated time
                # (from determine_slack)
                c_idle_new, c_activated_new = eval_context.schedule.optimize_scheduling()

                # Make sure new Schedule is _actually_ better - here, we
                # determine the nodes in last node receiving a message
                # in both schedules
                slowest_old = sorted(c_activated.items(), key=lambda x: x[1], reverse=True)
                slowest_new = sorted(c_activated_new.items(), key=lambda x: x[1], reverse=True)

                # Activate the new schedule
                c_idle, c_activated = c_idle_new, c_activated_new
                t_old = slowest_old[0][1]
                t_new = slowest_new[0][1]

                logging.info(('OPT sort %2d - %8.2f to %8.2f' % \
                                  (num_reorders, t_old, t_new)))
                num_reorders += 1

                # Sanity checks
                assert t_new - t_old <= 0.1 # rounding errors
                assert eval_context.schedule.cost_tree() <= cost_tree

                self.draw(eval_context)


            # Find LAST node
            # ------------------------------
            _last_node = sorted(c_activated.items(), key=lambda x: x[1], reverse=True)
            last_node, t_last_node = _last_node[0]

            for (core, time) in _last_node:
                logging.info(( 'first seen: %2d %8.2f' % (core, time)))


            # Find IDLE node that can deliver the message first
            # --------------------------------------------------

            # Calculate for each core how long it would take it to
            # deliver a message to (last) after finishing sending it's
            # current schedule
            #
            # Since we are interested in the latency, we should NOT
            # use the corrected times here. They are most likely
            # caused by some hardware optimization (write-buffer) and
            # just hide the cost of sending a message from the
            # sender. The latency of the send should be the same
            #
            # Generate tupple:
            # core         = the core ID
            # time         = time at wich idle
            # available_at = time at which message can be available at receiver
            fastest_send = []

            for (core, time) in c_idle.items():

                if eval_context.topology.has_edge((core, last_node)) or \
                   core == last_node:

                    continue

                t_prop = max(\
                    eval_context.model.get_send_cost(core, last_node, False, False),\
                    eval_context.model.get_send_cost(core, last_node, corrected=True))

                fastest_send.append((core, time, time + t_prop + \
                    eval_context.model.get_receive_cost(core, last_node)))

            logging.info(('eligible sender nodes' + str(fastest_send)))


            # That's the time at which a core is done sending a
            # messages. Cores that finish early have some slack to send to others
            fastest_send = sorted(fastest_send, key=lambda x: x[2])
            for (core, time, available_at) in fastest_send:
                logging.info(('could send from %2d at %8.2f starting %8.2f' \
                                % (core, available_at, time)))

            # Select best fitting sender core (first) and last core to
            # finish (last) - when only two cores are participating in
            # a broadcast, it is possible that fastest_send is empty
            # because there already is an edge between these two
            # nodes. In that case, we simply abort.
            if len(fastest_send)<1:
                optimize = False
                continue

            first, f_time, f_available_at = fastest_send[0]

            # Replace if:
            # 1) we have enough slack for an additonal message and
            # 2) the additional message is not already part of the schedule
            #
            # Check if (first->last) would optimize the tree
            if f_available_at < t_last_node and \
               not eval_context.topology.has_edge((first, last_node)):

                optimize = True

                # Sanity check
                c_slowest, t_slowest = eval_context.schedule.get_slowest()
                assert (last_node == c_slowest)
                assert (t_last_node == t_slowest)

                # ------------------------------
                # Replace edge
                #
                # This is a complicated task:
                #
                # 1. Update topology itself
                # 2. Update adaptive tree internal data structure
                # 3. Update the send history in the machine model
                # 4. Update the send history in the adaptie tree scheduler
                # ------------------------------
                eval_context.schedule.replace(first, last_node) # 2 + 4
                eval_context.model.update_edge(first, last_node, eval_context.topology) # 1 + 3
                # With 1-4, the send histories should be consistent again
                eval_context.schedule.assert_history()

                cost_tree_new = eval_context.schedule.cost_tree()

                logging.info(('OPT: shuffle %2d -> %2d - cost %8.2f to %8.2f' %\
                    (first, last_node, cost_tree, cost_tree_new)))

                self.draw(eval_context)

                # Evaluate cost of new topology - should be FASTER now
                assert cost_tree_new < cost_tree

            else:
                optimize = False

        # FINISHED OPTIMIZING
        # --------------------------------------------------
        # Update last node
        _, c_activated = eval_context.schedule.simulate_current()
        ln, _ = sorted(c_activated.items(), key=lambda x: x[1], reverse=True)[0]
        eval_context.last_node = ln

        return True


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
        logging.info(('Leaf nodes are', str(leaf_nodes)))

        for l in leaf_nodes:
            eval_context.schedule_node(l)

        self.parents = eval_context.topo.get_parents(eval_context.schedule)
        logging.info(('Parent relationship: ', self.parents))

        self.root = root


    def receive_handler(self, eval_context, core, from_core, time):

        self.num_msgs[core] = self.num_msgs.get(core, 0) + 1
        num = self.num_msgs[core]

        num_children = len([ x for (x, p) in self.parents.items() if p == int(core) ])

        logging.info((bcolors.OKBLUE + \
                          ('%d: Core %d receiving message %d/%d' %
                           (time, core, num, num_children)) + \
                          bcolors.ENDC))

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
        logging.info(('Count on', core, 'out of', num_children, 'is', num))

        if num >= num_children:
            logging.info(('Sending to parent', parent))

            # Send history should be empty, as only one message is
            # sent per node (to its parent)
            assert len(eval_context.model.send_history.get(core,[])) == 0

            send_compl = time + eval_context.model.get_send_cost(core, parent, True, True)

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
        logging.info(('Initializing new Barrier'))
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
        logging.info(('Leaf nodes are', str(leaf_nodes)))

        for l in leaf_nodes:
            logging.info(('barrier state: %d - %d' % (l, Barrier.REDUCE)))
            self.state[l] = Barrier.REDUCE
            eval_context.schedule_node(l)

        self.parents = eval_context.topo.get_parents(eval_context.schedule)
        logging.info(('Parent relationship: ', self.parents))

        self.root = root
        logging.info(('Setting root to %d', self.root))



    def idle_handler(self, eval_context, core, time):
        """
        """
        # Get a list of neighbors from the scheduler
        nb = eval_context.schedule.find_schedule(core, self.cores_active)
        assert isinstance(nb, list)
        assert isinstance(self.cores_active, list)

        # Ignore all nodes that received the message already
        nb_filtered = [ tmp for (_, tmp) in nb if tmp not in self.cores_active ]

        # --------------------------------------------------
        # Reduce state
        if self.state.get(core, Barrier.IDLE) == Barrier.REDUCE:

            logging.info((('Node %d is in reduce state and received a message '
                   'or no neighbors (%d)') % (core, len(nb_filtered))))

            # There is nothing to do for the root
            if core == self.root:
                logging.info(('node %d is root' % core))
                return

            self.num_msgs[core] = self.num_msgs.get(core, 0) + 1
            num = self.num_msgs[core] - 1
            plist = eval_context.topo.get_parents(eval_context.schedule)

            num_children = len([ x for (x, p) in plist.items() \
                                 if p == int(core) ])

            # Each core has only one parent - send a message there
            parent = eval_context.topo.get_parents(eval_context.schedule).get(core, None)
            assert parent != None # Unless we are the root, we have a parent
            logging.info(('Count on', core, 'out of', num_children, 'is', num))

            if num >= num_children:
                logging.info(('%d: Sending to parent %d (%d/%d)' %\
                                  (core, parent, num, num_children)))

                cost = eval_context.model.get_send_cost(core, parent, True, True)

                logging.info(('Send(%d,%s,%s) - Barrier - Reduce - NBs=%d - cost %d' % \
                    (eval_context.sim_round, str(core), str(parent), 1, cost)))

                send_compl = time + cost

                # Note: don't have to enqueue the same core as sender again
                eval_context.schedule_node(parent, send_compl, core)

        # --------------------------------------------------
        # Broadcast state
        elif len(nb_filtered) > 0:

            assert self.state[core] == Barrier.BC
            logging.info(('Node %d is in broadcast state and received a message ' % core))

            dest = nb_filtered[0]
            cost = eval_context.model.get_send_cost(core, dest, True, True)

            # Adaptive models: need to add edge
            if not eval_context.topology.has_edge((core,dest)):
                eval_context.topology.add_edge(
                    (core, dest),
                    eval_context.model.graph.edge_weight((core, dest)))

            eval_context.visu.send(core, dest, time, cost)
            logging.info(('Send(%d,%s,%s) - Barrier - BC - NBs=%d - cost %d' % \
                (eval_context.sim_round, str(core), str(dest),
                 len(nb_filtered), cost)))

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
        logging.info(('Receiving message on core %d' % core))

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
                logging.info(('barrier state: %d - %d' % (core, Barrier.REDUCE)))
                self.state[core] = Barrier.REDUCE

            return start_bc

        elif curr_core_state == Barrier.REDUCE:
            # Change state to BROADCAST, trigger sending a message
            logging.info(('barrier state: %d - %d' % (core, Barrier.BC)))
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

        logging.info(('Checking if Barrier is terminated - %d' % len(self.state)))

        reduce_done = True
        finished = True

        if len(self.state) < len(eval_context.model.get_cores(True)):
            logging.info(('Not all cores have seen the message %d/%d' % \
                          (len(self.state), len(eval_context.model.get_cores(True)))))
            m = eval_context.model
            sched = eval_context.schedule
            for c in m.get_cores(True):
                logging.info(( '%d -> %s' % \
                    (c, ','.join([ str(x) for (_, x) in sched.find_schedule(c) ]))))


            for i in eval_context.model.get_cores(True):
                if not i in self.state:
                    logging.info(('Core %d did not any message yet' % i))

            return False

        for (i, (core, state)) in enumerate(self.state.items()):
            if state != Barrier.BC:
                logging.info(('barrier:is_terminated(%d): !finished core=%d state=%d' %\
                              (i, core, state)))
                finished = False
            elif state != Barrier.REDUCE:
                logging.info(('barrier:is_terminated(%d): !reduce_done core=%d state=%d' %\
                              (i, core, state)))
                reduce_done = False

        logging.info(('barrier:is_terminated: finished=%d reduce_done=%d' %\
                      (finished, reduce_done)))

        if reduce_done:

            logging.info(('------------------------------'))
            logging.info(('REDUCE --> BROADCAST (from %d)' % self.root))
            logging.info(('------------------------------'))

            # Activate BC for root
            self.state[self.root] = Barrier.BC
            logging.info(('barrier state: %d - %d' % (self.root, Barrier.BC)))

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
        self.node_finished_list = [] # Nodes in the ordered they finished

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

        # AB twice for adaptive tree
        prots = [ AB(), Reduction(), Barrier() ]

        if topo.options.get('shuffle', False):
            prots = [ AB() ] + prots

        for protocol in prots:

            logging.info(('Evaluating protocol %s' % \
                protocol.get_name()))

            ev = Evaluate(protocol)
            # import cProfile
            # cProfile.run('ev = Evaluate(protocol)')
            # return None

            res.append((protocol.get_name(), ev.evaluate(topo, root, m, sched)))

            # Mark the schedule as finished, relevant for the adaptive
            sched.next_eval()

            # Reset send history
            m.reset()


        # Dump tree
        for c in m.get_cores(True):
            print( '%d -> %s' % \
                            (c, ','.join([ str(x) for (_, x) in sched.find_schedule(c) ])))

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

        # Determine order in which nodes where finished according to the Simulator
        self.nodes_by_receive_order = []

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
        logging.info(('Evaluate overlay', str(topo), 'using scheduler', str(sched), \
            'tree is', str(topo.get_tree())))

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

        final_time = self.sim_round
        r = Result(self.sim_round, self.last_node, visu_name)

        # Add cost for communication last_node -> root, since we will
        # evaluate the cost of the protocol in real hardware starting
        # at the last node. Do so only if the protocol requires it.
        if self.protocol.send_last_node():

            # If the last node would send further messages, it would not be the last node ..
            assert len(self.model.send_history.get(self.last_node, []))==0
            send_feedback = self.model.get_send_cost(self.last_node, root, True, True)

        else:
            send_feedback = 0

        print ("Terminating(%d,%s,%s) - cost %d for last_node -> root" % \
                    (self.sim_round, str(self.last_node), str(root),
                     send_feedback + self.model.get_receive_cost(self.last_node, root)))
        self.sim_round += send_feedback
        # * Propagation
        self.sim_round += T_PROPAGATE
        # * Receive cost
        self.sim_round += self.model.get_receive_cost(self.last_node, root);
        r.time = self.sim_round

        self.visu.finalize(int(final_time))

        # Determine order in which nodes where finished according to the Simulator
        r.node_finished_list = self.nodes_by_receive_order

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
        (p, e) = heapq.heappop(self.event_queue) # If this happens,
                  # there are no more events, but the protocol is
                  # still not terminated. This is most likely because
                  # the protocol did not terminate with is_terminated,
                  # despite the fact that there are no more messages
                  # floating around in the system. This should not
                  # happen.
        assert(p>=self.sim_round) # Otherwise, we pick up events that should have happened in the past
        self.sim_round = p

        d = int(e.dest) if e.dest != None else -1
        s = int(e.src) if e.src != None else -1

        if isinstance(e, events.Propagate):
            self.propagate(e.src, e.dest)

        if isinstance(e, events.Receive):
            self.receive(e.src, e.dest)

        if isinstance(e, events.Send):
            assert e.dest is None
            self.send(e.src)

        logging.info((bcolors.OKGREEN + \
            ('% 5d   core %d - %s -> Core %d' %
             (self.sim_round, s, e.get_type(), d)) + \
            bcolors.ENDC))


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
                logging.info((bcolors.BOLD + \
                    ('%d: Core %d propagete, found existing event %s at %d %d -> %d - ' %
                     (self.sim_round, dest, ev.get_type(), ts, ev.src, ev.dest)) + \
                    bcolors.ENDC))

                if isinstance(ev, events.Receiving):

                    _new = max(enqueue_at, ts)

                    logging.info((bcolors.BOLD + bcolors.FAIL + \
                        ('%d: Core %d is already receiving %d -> %d' %
                         (self.sim_round, dest, enqueue_at, _new)) +
                                  bcolors.ENDC))

                    assert ts >= enqueue_at
                    enqueue_at = _new

        w = T_PROPAGATE
        heapq.heappush(self.event_queue, (enqueue_at + w, events.Receive(src, dest)))

        # Node (src) has just sent a message, increment send batch size
        self.node_state[src].send_batch += 1

        logging.info(("% 5d   Propagate(%s->%s) - cost % 4d   done=% 5d" %\
                          (self.sim_round, str(src), str(dest), w, w + self.sim_round)))

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
        self.nodes_by_receive_order.append(dest)

        # Get receive cost
        cost = self.model.get_receive_cost(src, dest)
        self.visu.receive(dest, src, self.sim_round, cost)
        logging.info(("% 5d   Receive(%s->%s)  - cost % 4d   done=% 5d" \
                         % (self.sim_round, str(src), str(dest), cost, cost+self.sim_round)))

        # Node (src) has just received a mesage, reset send batch
        self.node_state[dest].send_batch = 0

        schedule_send = self.protocol.receive_handler( \
            self, dest, src, self.sim_round)

        # It's possible that there is another event scheduled for the
        # receiving node. In that case, we need to update the
        # timestamp accordingly.

        # Start updating the heap
        # --------------------------------------------------

        _heap = []

        for he in self.event_queue:
            (ts, ev) = he

            if ev.dest == dest or ev.src == dest:

                logging.info((bcolors.WARNING + \
                    ('%d: Core %d found another event %s at %d %d -> %d - ' %
                     (self.sim_round, dest, ev.get_type(), ts, ev.src, ev.dest)) + \
                    bcolors.ENDC))

            if ev.dest == dest and isinstance(ev, events.Receive):

                assert (ev.src != src) # this should be from a different source

                logging.info((bcolors.WARNING + \
                    ('%d: Core %d found another event %s at %d from %d - '
                     'cost: %d - new ts %d' %
                     (self.sim_round, dest, ev.get_type(), ts, ev.src,
                      cost, ts + cost)) + \
                    bcolors.ENDC))
                # assert (ts>=self.sim_round) # otherwise, we'd have an
                #                             # event on the queue that
                #                             # should have been
                #                             # executed BEFORE the
                #                             # current time.
                # active_event = max(active_event, ts)
                _heap.append((ts + cost, ev))

            else:
                _heap.append(he)

        # End updating the heap
        # --------------------------------------------------

        self.event_queue = _heap
        heapq.heapify(self.event_queue)

    #    print [ (ts, ev.src) for (ts, ev) in self.event_queue if \
#                ev.dest == dest and isinstance(ev, events.Receive) ]

        # Schedule a send? after the receive is complete
        if schedule_send:

            recv_cmpl = self.sim_round + cost
            logging.info((bcolors.OKBLUE + \
                ('% 5d   Core %d is scheduling a send operation %d at %d' %
                 (self.sim_round, dest, src, recv_cmpl)) + \
                 bcolors.ENDC))

            heapq.heappush(self.event_queue, (recv_cmpl, events.Send(dest, None)))

        else:

            recv_cmpl = self.sim_round + cost
            logging.info((bcolors.OKBLUE + \
                ('% 5d   Core %d is scheduling a DUMMY operation %d at %d' %
                 (self.sim_round, dest, src, recv_cmpl)) + \
                 bcolors.ENDC))

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
