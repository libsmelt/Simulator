#!/usr/bin/env python

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

import copy
import argparse
import Queue
import math
import threading
import time
from datetime import datetime

import config
from server import SimArgs

USE_THREADS=False

class bfThread(threading.Thread):
    def __init__(self, args):
        threading.Thread.__init__(self)
        self.args = args
    def run(self):
        brute_force(*self.args)

num_evaluated = 0

T_SEND=100
T_RECEIVE=50

# C*(n-1)!

threadLock = threading.Lock()
g_max = 0
g_min = type(sys.maxsize)

m = None
c_mapping = None

def send(s, r):
    if not m:
        return T_SEND
    else:
        return m.query_send_cost(c_mapping[s], c_mapping[r])

def receive(s, r):
    if not m:
        return T_RECEIVE
    else:
        return m.get_receive_cost(c_mapping[s], c_mapping[r])

def catalan_rec(n):
    """Calculate the Catalan number for n

    https://stackoverflow.com/questions/33958133/calculating-catalan-numbers
    """
    ans = 1.0
    for k in range(2,n+1):
        ans = ans *(n+k)/k
    return ans


def predict(n):
    """Predict how many models have to be evaluated for a tree of size n
    vertices.

    """
    C = catalan_rec(n)
    lowerbound = C
    upperbound = C*math.factorial(n-1)
    print 'Configurations for graph of size %d: lower-bound=%d, upper-bound=%d' % \
        (n, lowerbound, upperbound)


def output_tree(a, root, cost):
    """Output the given tree

    """
    print '--------------------------------------------------'
    print '%d nodes' % len(a), 'root', root, 'cost', cost
    for i, v in enumerate(a):
        print '%d (%d)-> %s (%s)' % (i, c_mapping[i],
                                     ','.join(map(str, v)),
                                     ','.join([ str(c_mapping[x]) for x in v]))



def evaluate(a, root):
    """Evaluate array given as argument a

    """

    q = Queue.Queue()
    q.put((root, 0))

    n_nodes = 0
    t_max = 0

    while not q.empty():

        c, time = q.get()
        assert c < len(a)

        n_nodes += 1

        if len(a[c]) == 0:
            # no leaf nodes
            t_max = max(t_max, time)

        # Sequential send
        for child in a[c]:
            time += send(c, child)
            q.put((child, time + receive(c, child)))


    assert n_nodes == len(a)

    global g_max, g_min, num_evaluated


    if t_max < g_min or t_max > g_max:

        if USE_THREADS:
            threadLock.acquire()

        # Compare with global max/min
        if t_max < g_min:
            # Found a new minimum:
            g_min = t_max
            output_tree(a, root, t_max)

        if t_max > g_max:
            # Found a new maximum:
            g_max = t_max
            output_tree(a, root, t_max)

        if USE_THREADS:
            threadLock.release()

    # num_evaluated += 1 # < Python does not seem to have an atomic
    #                    # increment, CAS or similar





def brute_force(N, unused_nodes, used_nodes, tree, root):
    """Brute-force a model of given size N

    This algorithm will generate the same tree in many cases. E.g. it
    can decide to attach node i followd by node j and then the other
    way round in a non-conflicting way, such that the trees are
    actually the same.

    """

    if used_nodes == None:

        # Initialize data structures
        used_nodes = []
        if (unused_nodes==None):
            global c_mapping
            c_mapping, unused_nodes = enumerate(range(N))
        tree = [ [] for i in range(N) ]

    if (N==0):
        evaluate(tree, root)

    use_threads = False

    # Sanity check
    assert len(unused_nodes) == N

    # We can choose any of the yet unused nodes
    for nxt in unused_nodes:

        unused_new = [ n for n in unused_nodes if n != nxt ]
        assert len(unused_nodes) == len(unused_new)+1

        if len(used_nodes) == 0:

            if USE_THREADS:

                t = bfThread((N-1, unused_new, [nxt], tree, nxt))
                t.setDaemon(True)
                t.start()

                use_threads = True

            else:
                brute_force(N-1, unused_new, [nxt], tree, nxt)

        # We can choose where we would like to attach the node, too
        for attach_at in used_nodes:

            # Construct new tree
            _tree = copy.deepcopy(tree)
            _tree[attach_at].append(nxt)

            brute_force(N-1, unused_new, used_nodes + [nxt], _tree, root)

    if not USE_THREADS:
        global num_evaluated
        num_evaluated += 1

    if use_threads:
        # We have been swaning threads in this execution of brute_force
        print 'Waiting for threads to finish'
        while threading.active_count() > 1:
            time.sleep(0.1)
        print 'Done'


def main():

    parser = argparse.ArgumentParser(description=('Brute-force check all trees for model of given size'))
    parser.add_argument('num', type=int, help='Size of the model')
    parser.add_argument('machine', help='Name of the machine for t_send and t_receive')
    parser.add_argument('--complexity', action='store_const', default=False, const=True)
    parser.add_argument('--cores', help='Coma separated list to evaluate')
    args = parser.parse_args()

    config.args = SimArgs()
    config.args.machine = args.machine

    global m

    m_class = config.arg_machine(args.machine)
    m = m_class()

    if args.complexity:
        predict(args.num)

    else:
        # ./brute-force.py 8
        # Evaluated 203212800 models
        #
        #             7207200 <- upper bound prediction


        unused_nodes = None
        if args.cores:
            global c_mapping
            print 'Using the following cores:', args.cores
            c_mapping = map(int, args.cores.split(','))
            unused_nodes = range(len(c_mapping))

        t1 = datetime.now()
        brute_force(args.num, unused_nodes, None, None, None)
        t2 = datetime.now()
        delta = t2 - t1
        print 'Evaluated %d models, time=%d [s]' % \
            (num_evaluated, delta.seconds)

        # tree = [ [] for i in range(args.num) ]
        # tree[0] = [1, 2, 3]
        # tree[2] = [4, 5]
        # evaluate(tree, 0)

if __name__ == "__main__":
    print threading.active_count()
    main()


## EARLY RESULTS
## --------------------------------------------------
##
##
## sbrinz1 - cores 0-6
##
## Simulator: Cost atomic broadcast for tree is: 2599 (1831), last node is 6
## Brute-force:
## 7 nodes root 2 cost 1683.949445
## 0 ->
## 1 -> 0
## 2 -> 5,1,4,3
## 3 ->
## 4 ->
## 5 -> 6
## 6 ->
## Evaluated 3628800 models
## Evaluated 3628800 models, time=300 [s]
##
## That's only 8% from the optimal

# Parallized: Evaluated 0 models, time=1349 [s]
