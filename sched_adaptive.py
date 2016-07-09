# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

import pdb
import logging
import random
import model
import Queue
import config

from pygraph.algorithms.minmax import shortest_path
from pygraph.classes.graph import graph
from pygraph.classes.digraph import digraph

# Number of messages to send to a remote NUMA node before stopping to
# do so
NUM_STOP_REMOTE=1

# --------------------------------------------------
class SchedAdaptive(scheduling.Scheduling):
    """Scheduler supporting dynamic creation of broadcast tree
    """

    """For each node <s>, Stores all outgoing connections (cost, r) that
    are used in the schedule, where r is the receiver and cost the
    cost associated with sending a message from s to r.

    """
    store = dict()

    num = 0
    finished = False

    def __init__(self, graph, mod, overlay):
        assert isinstance(mod, model.Model)
        self.mod = mod
        self.overlay = overlay
        self.store = {key: [] for key in range(self.mod.get_num_cores())}
        super(SchedAdaptive, self).__init__(graph)

    def _numa_domain_active(self, core, nodes_active):
        """
        Return whether at least one of the cores of the given NUMA
        domain is active

        """
        num = 0
        for c in self.mod.get_numa_node(core):
            if c in nodes_active:
                num += 1
        return num >= NUM_STOP_REMOTE

    def get_leafs(self):
        """Return a list of all leaf nodes in the current tree

        """
        _l = [ s for s, children in self.store.items() if len(children)==0 ]
        return _l

    def get_parents(self):
        """Return a dictionary core -> parent identifying each core's parent
        in the current tree.

        """
        _p = {}
        for s, children in self.store.items():
            for (_, child) in children:
                assert not child in _p # Each core has only one parent
                _p[child] = s
        return _p

    def get_root(self):
        """Returns the root of the current tree

        The root does not have a parent. So we need to find a node
        without parents.

        """
        parent = self.get_parents()
        for s, children in self.store.items():
            if not s in parent:
                return s
        raise Exception('Could not find root')


    def assert_faster(self, cost_prev):
        """Check if a new send scheduler is faster than the previous one.

        @param cost_prev The cost for the previous schedule, as
        returned by cost_subtree()

        """
        cost_new = self.cost_subtree()
        assert cost_new[self.get_root()] <= cost_prev[self.get_root()]



    def assert_history(self):
        """Sanity check to verify that the send history as known to the
        machine model matches the order as given from the adaptivetree.

        If this is true, we can use the build-in function
        get_send_cost() with the corrected option, as the send history
        as stored in the model matches the one in the adaptive tree.

        """

        for sender, children in self.store.items():

            # Retrieve send history for that node
            sh_them = self.mod.send_history.get(sender, [])

            # Drop the costs
            sh_us = [ n for (_, n) in children ]

            assert len(sh_them) == len(sh_us) # same number of children
            for us, them in zip(sh_us, sh_them):
                assert us == them # send history matches in each element

        print 'Send history is correct :-)'


    def cost_tree(self):
        return self.cost_subtree()[self.get_root()]


    def cost_subtree(self, node=None):
        """Determine the cost of each node as the cost of the entire subtree
        starting in that node.

        Returns the cost as a dictionary core -> cost at subtree.

        """

        if node == None:
            node = self.get_root()

        _, t_avail = self.simulate_current()

        # Determine maximum cost
        # --------------------------------------------------

        cost_st = {}

        cost_max = 0

        q = Queue.Queue()
        q.put(node)

        while not q.empty():
            c = q.get() # caluclate next core
            cost_max = max(cost_max, t_avail[c])

            # Get an order list of neighbors
            for _, nb in self.store[c]:

                q.put(nb)

        # Determine cost of subtree backwards
        # --------------------------------------------------


        q = Queue.Queue()
        for l in self.get_leafs():
            q.put(l)

        while not q.empty():

            core = q.get()
            if core in cost_st:
                continue

            c_cost = 0

            all_children = True
            for _, cld in self.store[core]:
                all_children &= cld in cost_st

            if not all_children:
                continue

            # Calculate the time difference for each child and take the max
            for _, cld in self.store[core]:

                assert t_avail[cld] > t_avail[core]
                cost_child_subtree = cost_st[cld]
                cost_connection = (t_avail[cld] - t_avail[core])
                c_cost = max(c_cost,  cost_child_subtree + cost_connection)

            cost_st[core] = c_cost

            for _, cld in self.store[core]:
                assert cost_st[core] > cost_st[cld]

            prt = self.get_parents()
            if core in prt:
                q.put(prt[core])


        # Root's subtree is the entire tree, i.e. the roots subtree
        # should equal the maximum cost of the entire tree
        assert (cost_max == cost_st[self.get_root()])

        return cost_st


    def reorder(self):

        """Optimize the current schedule.

        This does NOT change the topology, but only the send order in
        each node. Rather than sending on the most expensive _link_
        first, as generated in the initial unoptimized adaptive tree,
        we here changed the schedule to send to the most expensive
        _subtree_ of each child first

        However, the send history is affected by this. So, this
        function rewrites it while "simulating".

        Needs to be executed in 2 steps in order for the send
        histories to be consistent.

        """

        # Determine the cost of each subtree
        cost = self.cost_subtree()

        # reset send history in machine model
        self.mod.reset()

        new_store = {}

        # Find new order
        # ------------------------------
        for core, _children in self.store.items():

            # Determin children of a node
            children = [ c for (_, c) in _children ]

            # Get cost of each child's subtree
            children_cost = [ cost[c] for c in children ]

            # Sort, most expensive first
            children_sorted = sorted(zip(children, children_cost), \
                                     key=lambda x: x[1], reverse=True)

            new_store[core] = [ (_cost, _node) for (_node, _cost) in children_sorted ]


        self.store = {key: [] for key in range(self.mod.get_num_cores())}

        # Apply new order
        # ------------------------------
        for core, _children in new_store.items():

            for (cost, node) in _children:
                self.mod.add_send_history(core, node)
                self.store[core] = self.store.get(core, []) + [(cost, node)]

            logging.info(('Storing new send order', self.store.get(core, [])))

        assert self.get_root()

        # Fix send history
        self.assert_history()


    def get_slowest(self):

        _, t_avail = self.simulate_current()
        return sorted(t_avail.items(), key=lambda x: x[1], reverse=True)[0]


    def simulate_current(self, visu=None):

        # Send history
        send_history = {}

        # Calculate cost of subtree
        q = Queue.Queue()
        q.put((self.get_root(), 0))

        # Dictionary core c -> time when message is availabe on each
        # core, after receiving
        t_avail = {}

        # Dictionary core c -> time when core is idle, i.e. after
        # sending the last message. If no message is sent, this equals t_avail
        t_idle = {}

        # Determine the time where the message is available in each node
        # --------------------------------------------------

        while not q.empty():
            c, time = q.get() # caluclate next core

            assert not c in t_avail
            t_avail[c] = time

            # Get an order list of neighbors
            for _, nb in self.store[c]:

                # Send time as perceived by the client
                t_send = self.mod.get_send_cost_for_history(c, nb, send_history.get(c, []))
                assert t_send > 0

                # Actul send time
                t_send_propagate = max(self.mod.get_send_cost(c, nb, False, False), t_send)
                t_receive = self.mod.get_receive_cost(c, nb)

                # Visualize send and receive events
                if visu:
                    assert time + t_send <= time + t_send_propagate
                    visu.send(c, nb, time, t_send)
                    visu.receive(nb, c, time + t_send_propagate, t_receive)

                q.put((nb, time + t_send_propagate + t_receive))
                time += t_send
                send_history[c] = send_history.get(c, []) + [nb]

            assert not c in t_idle
            t_idle[c] = time # time after sending all messages OR
                             # after receiving if no message is sent.


        assert (len(t_avail)==len(self.store)) # Otherwise tree is not connected
        assert (len(t_idle) ==len(self.store)) # Otherwise tree is not connected

        return t_idle, t_avail


    def optimize_scheduling(self):
        """Find optimizations for current schedule.

        This is a 2-step process:

        1) Optimize the schedule - sort by cost of subtree rather than
        cost of individual link's cost. The send history is rebuild
        after this.

        Invariant: send history remains intact.

        """

        assert (len(self.store) == sum([len(c) for (s, c) in self.store.items()])+1)

        print 'root is', self.get_root()
        for core, children in self.store.items():
            print core, '->', [ core for (_, core) in children ]

        # --------------------------------------------------
        # REORDER - for each core, reorder messages
        #           most expensive subgraph first
        # --------------------------------------------------

        self.reorder()
        self.assert_history()

        return self.simulate_current()


    def replace(self, sender, receiver):
        """Updates the adaptive tree

        Remove (x, receiver) and add (sender, receiver) instead.
        """
        logging.info(('ADAPTIVE before' + str(self.store)))

        # Determine send cost before messing around with the send histories
        self.assert_history() # still intact, but we also don't use them elsewehere
        cost = self.mod.get_send_cost(sender, receiver)

        # Remove previous sender
        for (s, l_receivers) in self.store.items():
            logging.info(('ADAPTIVE', 'looking for ', receiver, 'in', l_receivers))
            self.store[s] = [ (cost, r) for (cost, r) in l_receivers if \
                              r != receiver ]

        # Add new pair
        self.store[sender].append((cost, receiver))

        logging.info(('ADAPTIVE after' + str(self.store)))


    def find_schedule(self, sending_node, cores_active=None):

        """
        Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @param cores_active List of active nodes
        @return A list containing all inactive nodes sorted by cost.
        """

        # We calculate the adaptive tree only once. After we finished
        # this, we just return whatever tree was generated in the
        # first iteration.

        if self.finished:
            return self.store[sending_node]

        assert cores_active is not None
        assert sending_node in cores_active

        cheap_first = self.overlay.options.get('min', False)

        self.num += 1
        #print 'Active nodes - %d' % self.num, len(cores_active)

        # Find cores that ...
        # Principles are:
        # * The filter makes sure that we do _not_ send unnecessary messages
        #     across NUMA domains
        # * Send expensive messages first
        cores = self.graph.nodes()
        inactive_nodes = []

        for c in cores:

            # Never send to ourself
            if c == sending_node:
                continue

            # Do not consider any nodes that are not in the multicast
            if not c in self.mod.get_cores(True):
                continue

            logging.info('Sending node from %d to %d' % (sending_node, c))

            # Is the target node active already?
            node_active = self._numa_domain_active(c, cores_active)

            # Is the target core on the sender's local node?
            # but we did not yet send it there before
            same_node = self.mod.on_same_numa_node(sending_node, c)

            # Shoulds this node be considered for sending?
            if cheap_first:
                # Consider all cores to which we are not sending a message yet
                consider = not c in cores_active
            else:
                # Yes, if receiver is on inactive node, or on local node
                consider = not node_active or same_node

            # Do not resent messages to local cores. The local node is
            # already active at that point, so remove nodes will not
            # recent messages to any of the cores on that node.
            #
            # What remains to be checked is whether any of the other
            # cores on the same node already sent a message.
            if same_node or True:

                # Check if somebody else sent a message there already
                for othercores in self.mod.get_numa_node(sending_node):
                    if c in [s for (_,s) in self.store[othercores]]:

                        logging.info('Not considering %d, as message was already sent' % c)
                        consider = False

                # Check if node is already active (e.g. the root,
                # which no one sent a message to already
                if c in cores_active:
                    logging.info('Not considering %d, already active' % c)
                    consider = False


            # If we consider this core, it's node is inactive, which
            # means that c is inactive itself.
            assert not consider or not c in cores_active

            if consider:
                # build (cost, core) tuple
                # Here, we use send + receive time as the cost, as we are
                # looking for a metric that estimates the total cost of
                # sending a message across - not just from the perspective
                # if the sender
                inactive_nodes.append((self.mod.get_send_cost(sending_node, c, False, False)+\
                                       self.mod.get_receive_cost(sending_node, c), c))

            logging.info('%s %d -> %d, as node_active=%d and same_node=%d' % \
                ('Considering' if consider else 'Not sending', \
                 sending_node, c, node_active, same_node))


        logging.info("inactive_nodes from %d with cost: %s" % \
            (sending_node, inactive_nodes))

        # Prefer expensive links
        should_reverse = False if cheap_first else True
        inactive_nodes.sort(key=lambda tup: tup[0], reverse=should_reverse)
        logging.info("   sorted: %s" % (inactive_nodes))

        if len(inactive_nodes)==0:
            return []

        # Return only one node
        (_, next_r) = inactive_nodes[0]
        logging.info('Choosing %d' % next_r)

        # Replace target core (which is the most expensive node in the
        # system), with the cheapest on that node for remote nodes,
        # For local nodes, just send to the previously selected one,
        # which is already the most expensive one on that node.

        # Assumption: fully-connected model

        # All nodes on receivers node and their cost for current sender
        # Here, we only consider the send time, as we want to minimize time
        # spent on the sender

        if self.mod.on_same_numa_node(next_r, sending_node):
            # LOCAL SEND
            # --------------------------------------------------
            next_hop = (self.mod.get_send_cost(sending_node, next_r, False, False), next_r)

        else:
            # REMOTE SEND
            # --------------------------------------------------
            # Add other cores from same remote node, but ONLY if they are
            # multicast members. Essentiall, this means that we selected
            # the NUMA node to send to and now, we want to select the
            # cheapest core on that node.
            # --------------------------------------------------
            c_all = self.mod.filter_active_cores(self.mod.get_numa_node(next_r), True)
            c_all = [ c for c in c_all if not c in cores_active ]
            c_cost = [ (self.mod.get_send_cost(sending_node, r, False, False), r) \
                       for r in c_all if r != sending_node ]
            # Sort, cheapest node first
            c_cost.sort(key=lambda tup: tup[0])
            logging.info(('Other cores on that node: %s ' % str(c_cost)))

            # Pick first - but list returned needs to have same length
            # as number of inactive nodes
            next_hop = (c_cost[0][0], c_cost[0][1])

        # Remember choice
        assert next_hop not in self.store[sending_node]
        # Otherwise, we already sent a message to the same core

        self.store[sending_node].append(next_hop)
        logging.info(("Targets from", sending_node, ":", self.store[sending_node]))

        return [next_hop]


    def get_final_schedule(self, sending_node, active_nodes=None):
        """Return schedule previously found by iterative find_schedule calls.

        Note: the final schedule does NOT need the cost! Also,
        reordering does NOT need the cost. The cost here is what was
        previously stored in self.store

        """
        try:
            res = [(None, r) for (_, r) in self.store[sending_node]]
            logging.info(('Node', sending_node, 'is sending a message to', \
                [ r for (_, r) in res ]))
            return res
        except:
            logging.info(('Node', sending_node, 'is not sending any message'))
            return []

    def next_eval(self):
        print '--------------------------------------------------'
        print 'FINISHED'
        print '--------------------------------------------------'
        self.finished = True


    def visualize(self, m, topo):

        if not config.args.debug:
            return

        import draw
        d = draw.Output('visu.tex', m, topo)
        _, t_avail = self.simulate_current(d)
        d.finalize(int(max([ t for (_, t) in t_avail.items()])))
        d.generate_image()

        raw_input("Press the <ENTER> key to continue...")

        import subprocess, shlex
        subprocess.check_call(shlex.split('cp visu.png visu-old.png'))
