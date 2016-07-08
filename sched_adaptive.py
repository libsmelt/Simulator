# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

import pdb
import logging
import random
import model
import Queue

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
                print 'Found parent of', child, 'to be', s
                _p[child] = s
        return _p

    def get_root(self):
        """Returns the root of the current tree

        """
        parent = self.get_parents()
        for s, children in self.store.items():
            if not s in parent:
                return s
        raise Exception('Could not find root')


    def cost_subtree(self):
        """Determine the cost of each node as the cost of the entire subtree
        starting in that node.


        Returns the cost as a dictionary core -> cost at subtree.

        """

        leafs = self.get_leafs()
        parent = self.get_parents()

        # Calculate cost of subtree
        q = Queue.Queue()
        for l in leafs:
            q.put(l)

        # Directonary core c -> cost of subtree of core c including
        # the receive from parent
        cost = {}

        while not q.empty():
            c = q.get() # caluclate next core

            # It is possible that the same core is added to the queue
            # repeatedly from several children
            if c in cost:
                continue

            print 'Looking at core', c

            # Determine parent node
            c_parent = parent[c] if c in parent else None

            # Receive from parent
            c_cost = self.mod.get_receive_cost(c_parent, c) if c_parent else 0

            # Add cost of all children's subtrees, if available
            all_children = True
            for _, child in self.store[c]:
                if not child in cost:
                    print 'Warning', child, 'not yet in queue'
                    all_children = False
                    break
                c_cost += self.mod.get_send_cost(c, child, corrected=True)
                c_cost += cost[child]

                # Note: core c will not be in the FIFO queue any
                # longer, but added again later by the at least one
                # remaining child

            if all_children:
                # Store cost of now compete subtree
                assert not c in cost
                cost[c] = c_cost

                # Put parent into FIFO queue
                if c_parent != None:
                    q.put(c_parent)
                else:
                    print 'Core', c, 'does not have a parent'



        assert (len(cost)==len(self.store)) # Otherwise tree is not connected
        print cost

        return cost


    def reorder(self):

        """Optimize the current schedule.

        This does NOT change the topology, but only the send order in
        each node. Rather than sending on the most expensive _link_
        first, as generated in the initial unoptimized adaptive tree,
        we here changed the schedule to send to the most expensive
        _subtree_ of each child first
        """

        cost = self.cost_subtree()
        old_store = self.store.items()

        for core, _children in old_store:

            # Determin children of a node
            children = [ c for (_, c) in _children ]

            # Get cost of each child's subtree
            children_cost = [ cost[c] for c in children ]

            # Sort, most expensive first
            children_sorted = sorted(zip(children, children_cost), \
                                     key=lambda x: x[1], reverse=True)

            self.store[core] = [ (0, c) for (c, _) in children_sorted ]
            print 'Storing new send order', self.store[core]


    def optimize_scheduling(self):

        """Optimizes the current scheduling.

        Instead of sending on the most expensive link first, we should
        send to the most expensive subtree first"""

        assert (len(self.store) == sum([len(c) for (s, c) in self.store.items()])+1)

        print 'root is', self.get_root()
        for core, children in self.store.items():
            print core, '->', [ core for (_, core) in children ]

        # This does not work with results from the multi-message bench yet
        assert self.mod.mm == None

        # --------------------------------------------------
        # REORDER - for each core, reorder messages
        #           most expensive subgraph first
        # --------------------------------------------------

        self.reorder()

        # --------------------------------------------------
        # RECALCULATE - when do cores first receive a message
        # --------------------------------------------------

        log_first_message = {}
        log_idle = {}

        ac = Queue.Queue()
        ac.put((self.get_root(), 0))

        while not ac.empty():

            c, time = ac.get()
            log_first_message[c] = time

            for _, child in self.store[c]:

                # global time, increases with each child
                time += self.mod.get_send_cost(c, child, corrected=True)

                # XXX propagate here

                # happens asynchronously, so we don't update the time
                cost = self.mod.get_receive_cost(c, child)

                # append new event
                ac.put((child, time + cost))

            # this core is idle now
            log_idle[c] = time


        print "log idle"
        print log_idle

        print "log first message"
        print log_first_message

        assert len(log_idle) == len(self.store)
        assert len(log_first_message) == len(self.store)

        return log_idle, log_first_message

    def replace(self, sender, receiver):
        """Updates the adaptive tree

        Remove (x, receiver) and add (sender, receiver) instead.
        """
        print 'ADAPTIVE before' + str(self.store)


        # Find previous sender
        for (s, l_receivers) in self.store.items():
            print 'ADAPTIVE', 'looking for ', receiver, 'in', l_receivers
            self.store[s] = [ (cost, r) for (cost, r) in l_receivers if \
                              r != receiver ]

        # Add new pair
        self.store[sender].append((0, receiver))

        print 'ADAPTIVE after' + str(self.store)

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
