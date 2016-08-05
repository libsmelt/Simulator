#!/usr/bin/env python

import sys
import os
sys.path.append(os.getenv('HOME') + '/bin/')

import re
import helpers
import logging

from topology_parser import on_same_node

class MultiMessage(object):

    @staticmethod
    def parse(f, topology, mode_list=[ 'last', 'sum' ]):
        """Parse the given MultiMessage benchmark file

        """

        sender_core = None
        data = {}
        err = {}
        history = {}

        cores_local = 0
        cores_remote = 0

        tsc_overhead = -1            # << TSC overhead read from  output

        for line in f.readlines():

            # Format:
            # cores=01,02,03,04,08,12,16,20,24,28, mode=all , avg=109, stdev=13, med=106, min=98, max=355 cycles, count=1800, ignored=3200
            m = re.match('cores=([0-9,]+), mode=([^,]+), avg=(\d+), stdev=(\d+), med=(\d+), min=(\d+), max=(\d+) cycles, count=(\d+), ignored=(\d+)', line)
            if m :
                cores = map(int, m.group(1).split(','))

                l_cores = []
                r_cores = []

                logging.info('Found cores' + str(cores))
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

                logging.info(('local', l_cores))
                logging.info(('remote', r_cores))

                l = len(l_cores)
                r = len(r_cores)

                mode = m.group(2).rstrip()
                logging.info(('found l=', l, 'r=', r, 'sender=', sender_core, \
                              'cores=', cores, 'mode=', mode, 'value=', int(m.group(3))))

                if not mode in data:
                    continue

                data   [mode][r][l] = int(m.group(3)) # arr[r][l]
                err    [mode][r][l] = int(m.group(4))
                history[mode][r][l] = cores # remember which core where used for that batch


            m = re.match('Calibrating TSC overhead is (\d+) cycles', line)
            if m:
                logging.info("TSC " + m.group(1))
                tsc_overhead = int(m.group(1))

            # num_cores: local=7 remote=3
            m = re.match('num_cores: local=(\d+) remote=(\d+)', line)
            if m:
                cores_local = int(m.group(1)) + 1
                cores_remote = int(m.group(2)) + 1
                logging.info("num_local_cores "  + str(cores_local))
                logging.info("num_remote_cores " + str(cores_remote))

                for l in mode_list: # arr[r][l]
                    data[l] =    [[0  for i in range(cores_local)] for j in range(cores_remote)]
                    err[l] =     [[0  for i in range(cores_local)] for j in range(cores_remote)]
                    history[l] = [[[] for i in range(cores_local)] for j in range(cores_remote)]

            # sender: 12
            m = re.match('sender: (\d+)', line)
            if m:
                sender_core = int(m.group(1))
                logging.info("sender is: " + str(sender_core))

        return (sender_core, cores_local, cores_remote, tsc_overhead, data, err, history)


    def __init__(self, _input, machine):
        """Initiate the multimessage parser.

        @param Instance of the machine to create the multimessage benchmark for

        """

        self.machine = machine

        tmp = MultiMessage.parse(_input, machine.machine_topology)
        self.sender_core, self.cores_local, self.cores_remote, \
            self.tsc_overhead, self.data, self.err, self.history = tmp

        self.history = self.history['sum']

        self.init_matrix()


    def init_matrix(self):
        """Initiliaze the multimessage matrix.

        This is a "correction" matrix. For each multimessage
        configuration of sending r remote and l local messages,
        calculate how much the cost of the same send history using
        n-receive is off.

        """

        self.matrix = [[ 0 for l in range(self.cores_local) ] for r in range(self.cores_remote)]

        for r in range(self.cores_remote)[::-1]:
            print '>> ',
            for l in range(self.cores_local):

                if r==0 and l==0:
                    print '                         |',
                    continue

                # Determine send cost as predicted by n-receive
                send_pw = self.machine.get_send_history_cost(self.sender_core, self.history[r][l])
                rel_error = send_pw/float(self.data['sum'][r][l])

                cost_last = self.data['last'][r][l] - self.tsc_overhead

                self.matrix[r][l] = rel_error

                print ' %5.1f %5.0f %5.0f %5.2f |' % \
                    (cost_last, self.data['sum'][r][l], send_pw, rel_error),

            print ''


    def get_factor(self, sender, c_batch):
        """Determine the correction factor for the given send batch <c_batch>
        starting from core sender

        """

        c_local = 0
        c_remote = 0

        for c in c_batch:
            if self.machine.on_same_numa_node(sender, c):
                c_local += 1
            else:
                c_remote += 1
                if c_local > 0:
                    helpers.warn('mm: adding remote communication AFTER local communication')

        assert c_local>0 or c_remote>0

        while c_local >= self.cores_local:
            helpers.warn('mm matrix local exceeded %d -> %d' % (c_local, self.cores_local))
            c_local -= 1

        while c_remote >= self.cores_remote:
            helpers.warn('mm matrix remote exceeded %d -> %d' % (c_remote, self.cores_remote))
            c_remote -= 1

        return self.matrix[c_remote][c_local]
