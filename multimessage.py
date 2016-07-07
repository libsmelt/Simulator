#!/usr/bin/env python

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

import numpy
import matplotlib.pyplot as plt
import matplotlib
import re
import helpers
import config

MAX=1000 # choose bigger than #local and #remote

from topology_parser import on_same_node

class MultiMessage(object):

    @staticmethod
    def parse(f, topology, mode_list):
        """Parse the given MultiMessage benchmark file

        """

        sender_core = None
        data = {}
        err = {}
        history = {}

        cores_local = 0
        cores_remote = 0

        tsc_overhead = -1            # << TSC overhead read from  output

        for line in f:

            # Format:
            # cores=01,02,03,04,08,12,16,20,24,28, mode=all , avg=109, stdev=13, med=106, min=98, max=355 cycles, count=1800, ignored=3200
            m = re.match('cores=([0-9,]+), mode=([^,]+), avg=(\d+), stdev=(\d+), med=(\d+), min=(\d+), max=(\d+) cycles, count=(\d+), ignored=(\d+)', line)
            if m :
                cores = map(int, m.group(1).split(','))

                l_cores = []
                r_cores = []

                print 'Found cores', str(cores)
                assert sender_core != None

                local = False # we execute remote sends first
                for c in cores:
                    _local = on_same_node(topology, sender_core, c)
                    assert not local or _local # no local message after remote ones
                    local = _local

                    if _local:
                        l_cores.append(c)
                    else:
                        r_cores.append(c)

                print 'local', l_cores
                print 'remote', r_cores

                l = len(l_cores)
                r = len(r_cores)

                mode = m.group(2).rstrip()
                print 'found l=', l, 'r=', r, 'sender=', sender_core, \
                               'cores=', cores, 'mode=', mode, 'value=', int(m.group(3))

                if not mode in data:
                    continue

                data   [mode][r][l] = int(m.group(3)) # arr[r][l]
                err    [mode][r][l] = int(m.group(4))
                history[mode][r][l] = cores # remember which core where used for that batch


            m = re.match('Calibrating TSC overhead is (\d+) cycles', line)
            if m:
                print "TSC " + m.group(1)
                tsc_overhead = int(m.group(1))

            # num_cores: local=7 remote=3
            m = re.match('num_cores: local=(\d+) remote=(\d+)', line)
            if m:
                cores_local = int(m.group(1)) + 1
                cores_remote = int(m.group(2)) + 1
                print "num_local_cores "  + str(cores_local)
                print "num_remote_cores " + str(cores_remote)

                for l in mode_list: # arr[r][l]
                    data[l] =    [[0  for i in range(cores_local)] for j in range(cores_remote)]
                    err[l] =     [[0  for i in range(cores_local)] for j in range(cores_remote)]
                    history[l] = [[[] for i in range(cores_local)] for j in range(cores_remote)]

            # sender: 12
            m = re.match('sender: (\d+)', line)
            if m:
                sender_core = int(m.group(1))
                print "sender is: ", sender_core

        return (sender_core, cores_local, cores_remote, tsc_overhead, data, err, history)


    def __init__(self, _input=sys.stdin, mmtype='last'):
        """Initiate the multimessage parser.

        @param mmtype: Choose the type of multimessage to use. Supported are:
            'last', 'all'"""

        # Initialize
        self.res = [[ None for j in range(MAX) ] for i in range(MAX) ]

        num_read = 0
        self.max_local = 0
        self.max_remote = 0

        # Parse input lines
        for line in _input:
            m = re.match('r=(\d+),l=(\d+), mode=([^,]+), avg=(\d+), stdev=(\d+), med=(\d+), min=(\d+), max=(\d+) cycles, count=(\d+), ignored=(\d+)', line)
            if m :
                l = int(m.group(2))
                r = int(m.group(1))
                mode = m.group(3).rstrip()

                if mode != mmtype:
                    continue

                rem, loc = tuple([ int(m.group(i)) for i in [1, 2]])
                avg, stdev, med = tuple([ float(m.group(i)) for i in [4, 5, 6]])

                # Sanity checks
                _check = abs(1.0-avg/med)
                if _check>0.1:
                    helpers.warn('WARNING: avg/med more than 10% apart ' + str(_check) + ' for ' + str((rem, loc)))

                _check = stdev/avg
                if _check>0.1:
                    helpers.warn('WARNING: avg/med more than 10% apart ' + str(_check) + ' for ' + str((rem, loc)))

                assert self.res[rem][loc] == None # otherwise we would have several
                                             # results for the same data
                self.res[rem][loc] = (avg, stdev, med)
                self.max_local = max(self.max_local, loc)
                self.max_remote = max(self.max_remote, rem)
                num_read += 1

    def get_factor(self, num_remote, num_local, local=True):
        """@param local Whether the message to be sent now (and who's cost to
        look up) is local

        """
        # Add the new message (whos type is indicated by local parameter)
        if local:
            num_local += 1
        else:
            num_remote += 1

        if num_remote > self.max_remote and num_local == 0:
            cost = self.res[self.max_remote][1][0]
        else:
            num_remote = min(self.max_remote, num_remote)
            cost = self.res[num_remote][num_local][0]

        return cost




    def get_factor_old(self, num_remote, num_local, local=True):
        """@param local Whether the message to be sent now (and who's cost to
        look up) is local

        """

        # The measurements are the accumulated send cost; we are
        # interested in the difference to the previous history,
        # i.e. if we are now sending message n(k), we are taking
        # n(1) .. n(k-1), take the difference of that and compare
        # it to n(1), the cost of sending just one message, which
        # is encoded in the pairwise results
        prev = self.res[num_remote][num_local][0] if \
               num_remote != 0 or num_local != 0 else 0

        # Add the new message (whos type is indicated by local parameter)
        if local:
            num_local += 1
        else:
            num_remote += 1

        if self.res[num_remote][num_local] == None :
            print "num_remote=%d, num_local=%d" % (num_remote, num_local)
        assert not self.res[num_remote][num_local] == None

        # Get baseline
        baseline = self.res[0][1] if local else self.res[1][0]

        # Cost when adding new send operation
        nxt = self.res[num_remote][num_local][0]
        last_snd_cost = nxt - prev # cost of the additional, new
                                   # message, not yet accounted for

        # XXX Have warning here that pops up when the std error is too high

        if last_snd_cost>0:
            return (last_snd_cost) / baseline[0]

        else:
            # This is a weird case from broken measurement: the cost
            # of sending one more message is than SMALLER than the
            # cost of sending all the messages in the history apart
            # from the last one. I.e. sending one more message makes
            # the cost SMALLER - we treat this by just returning a
            # factor 1.0
            helpers.warn('multimessage: send_cost < 0 - using factor of 1.0')
            return 1.0
