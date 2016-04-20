# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import scheduling

import pdb
import logging
import random
import model

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

    def __init__(self, graph, mod):
        assert isinstance(mod, model.Model)
        self.mod = mod
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


    def find_schedule(self, sending_node, cores_active=None):
        """
        Find a schedule for the given node.

        @param sending_node Sending node for which to determine scheduling
        @param cores_active List of active nodes
        @return A list containing all inactive nodes sorted by cost.
        """
        if self.finished:
            return self.store[sending_node]

        assert cores_active is not None
        assert sending_node in cores_active
        
        self.num += 1
        print 'Active nodes - %d' % self.num, len(cores_active)

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
                inactive_nodes.append((self.mod.query_send_cost(sending_node, c)+\
                                       self.mod.get_receive_cost(sending_node, c), c))

            logging.info('%s %d -> %d, as node_active=%d and same_node=%d' % \
                ('Considering' if consider else 'Not sending', \
                 sending_node, c, node_active, same_node))

            
        logging.info("inactive_nodes from %d with cost: %s" % \
            (sending_node, inactive_nodes))

        # Prefer expensive links
        inactive_nodes.sort(key=lambda tup: tup[0], reverse=True)
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
            next_hop = (self.mod.query_send_cost(sending_node, next_r), next_r)
            
        else:
            # Add other cores from same node, but ONLY if they are
            # multicast members
            c_all = self.mod.filter_active_cores(self.mod.get_numa_node(next_r), True)
            c_all = [ c for c in c_all if not c in cores_active ]
            c_cost = [ (self.mod.query_send_cost(sending_node, r), r) \
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
        """
        Return schedule previously found by iterative find_schedule calls.

        """
        try:
            res = [(None, r) for (c, r) in self.store[sending_node]]
            logging.info(('Node', sending_node, 'is sending a message to', \
                [ r for (_, r) in res ]))
            return res
        except:
            logging.info(('Node', sending_node, 'is not sending any message'))
            return []

    def next_eval(self):
        self.finished = True
        
