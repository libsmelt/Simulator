#!/usr/bin/python
import matplotlib
matplotlib.use('Agg')

import numpy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.pyplot import cm

import numpy as np

import json
import gzip
import re

import sys
import os

import matplotlib.cm as cm

from topology_parser import on_same_node, parse_machine_db

import matplotlib
from multimessage import MultiMessage

from config import MACHINE_DATABASE
MDB= '%s/' % MACHINE_DATABASE

sys.path.append(MDB)
import machineinfo

global m_class
m_class = None

fontsize = 14
mode_list = [ 'last', 'sum' ]

# CONFIGURE FONT
# --------------------------------------------------

PRESENTATION=False           # << font + colors
OUTPUT_FOR_POSTER=False      # << higher resolution

SENDER_CORE=None             # << for distinction local vs remote - given by output

tsc_overhead = -1            # << TSC overhead read from  output

import matplotlib
matplotlib.rcParams['figure.figsize'] = 12.0, 4.0
plt.rc('legend',**{'fontsize':fontsize, 'frameon': 'false'})
matplotlib.rcParams.update({'font.size': fontsize, 'xtick.labelsize':fontsize, 'ytick.labelsize':fontsize})

from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)

if not PRESENTATION:
    matplotlib.rc('font', family='serif')
    matplotlib.rc('font', serif='Times New Roman')
    matplotlib.rc('text', usetex='true')

def configure_plot(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

label_lookup = {
    'ab': 'atomic broadcast',
    'barriers': 'barrier',
    'agreement': '2PC'
}

def do_plot(cores_remote, cores_local, z, e, h, d, mode, machine, show_accurracy=False):
    """Plot data

    @param show_accurracy If set, rather than printing the measured
    values, generate a new heat-map with the accurracy of the raw
    n-send data, when applied to each core in the send history
    compared to the measured "sum" data.

    """
    # PREPARE heat map plot
    # --------------------------------------------------

    print h

    # make these smaller to increase the resolution
    dx, dy = 1.0, 1.0 # 0.15, 0.05

    # generate grid for the x & y bounds
    Y, X = np.mgrid[slice(0, cores_remote+1, dy),
                    slice(0, cores_local+1, dx)]

    _vmin = None
    _vmax = None
    Z = z.copy()

    if show_accurracy:
        for r in range(0,cores_remote):
            for l in range(0, cores_local):

                if r==0 and l==0:
                    continue

                # Get cost of history
                pairwise_cost = m_class.get_send_history_cost(SENDER_CORE, h[r][l])

                Z[r][l] = pairwise_cost/float(d['sum'][r][l])
                _vmin = 0.0
                _vmax = 2.0


    fig, ax = plt.subplots()

    plt.pcolor(X, Y, Z, cmap=tab_cmap, vmin=_vmin, vmax=_vmax)
    cb = plt.colorbar()

    color=cm.rainbow(numpy.linspace(0,1,cores_remote))

    # PRINT MEASUREMENTS
    # --------------------------------------------------

    for r in range(0,cores_remote):
       for l in range(0, cores_local):

            if r==0 and l==0:
                continue

            color = 'black'
            pairwise_cost = m_class.get_send_history_cost(SENDER_CORE, h[r][l])

            x = l
            y = r

            # Output multimessage + cores
            #label = '%.0f %s' % (z[r][l], ','.join(map(str,h[r][l])))

            # Output multimessage + pairwise estimate + std error
            #label = '%.0f %.f (%.0f)' % (z[r][l], pairwise_cost, e[r][l])

            # Output multimessage + pairwise estimate + relative error
            rel_error = pairwise_cost/float(d['sum'][r][l])
            label = '%.0f %.f (%.3f)' % (z[r][l], pairwise_cost, rel_error)

            plt.text(x + 0.5, y + 0.5, label,
                     horizontalalignment='center',
                     verticalalignment='center',
                     color=color,
                     fontsize=9)


    # CONFIGURE AXIS
    # --------------------------------------------------

    ax.set_xticks([ i + 0.5 for i in range(cores_local)])
    ax.set_xticklabels([ str(i) for i in range(cores_local) ])
    ax.set_xlim(xmin=0,xmax=cores_local)

    ax.set_yticks([ i + 0.5 for i in range(cores_remote)])
    ax.set_yticklabels([ str(i) for i in range(cores_remote) ])
    ax.set_ylim(ymin=0,ymax=cores_remote)

    plt.xlabel('number of local messages')
    plt.ylabel('number of remote messages')


    # OUTPUT
    # --------------------------------------------------
    plt.tight_layout() # re-create bounding-box

    f = '%s/%s/multimessage-%s.pdf' % (MDB, machine, mode)
    print 'Writing output', f
    plt.savefig(f)



def plot_multimesage(machine, f, output_last=True, calc_diff=True):
    """Evaluate multimessage benchmark

    \param output_last: Use the cost of the last message as output or
    the cost of the whole history

    \param calc_diff: If using the cost of the whole history, should I
    set this in relation to the cost of the history without the last
    message?

    """

    global SENDER_CORE

    topology = parse_machine_db(machine)
    print "parsing multimessasge for " + machine

    cores_total = 0

    # PARSE INPUT
    # --------------------------------------------------
    tmp = MultiMessage.parse(f, topology, mode_list)
    SENDER_CORE, cores_local, cores_remote, tsc_overhead, data, err, history = tmp



    assert tsc_overhead >= 0
    if 'last' in mode_list:
        for r in range(cores_remote):
            for l in range(cores_local):
                if r==0 and l==0:
                    continue

                data['last'][r][l] -= tsc_overhead

    #  Substract TSC

    # Calculate "sum" results - these are only meaningful if
    # subtracted from the previous result.
    #
    # We need to determine the cost of the last message by comparing
    # the cost of the current send batch with the cost of the one
    # smaller send batch.
    for r in range(cores_remote):
        for l in range(cores_local):

            if r+l < 2: # Nothing to do, for one message, the "sum"
                        # equals the cost of the last message
                continue

            l_ = l
            r_ = r

            if l>1:
                l_ = l-1
            else:
                r_ = r-1

            data['sum'][r][l] -= data['sum'][r_][l_]


    for m in mode_list:
        z = np.zeros((cores_remote, cores_local), dtype=np.float) # arr[r][l]
        e = np.zeros((cores_remote, cores_local), dtype=np.float)
        for r in range(cores_remote):
            for l in range(cores_local):
                if data[m][r][l] == 0:
                    print 'Warning', m, r, l, 'is 0'
                z[r][l] =    data[m][r][l]
                e[r][l] =     err[m][r][l]

        do_plot(cores_remote, cores_local, z, e, history[m], data, m, machine, arg.accuracy)



import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--machines')
parser.add_argument('--accuracy', help=('Accuracy of the raw n-receive measurements compared'
                                        'to the real execution of the send history'),
                    dest='accuracy', action='store_true')
parser.set_defaults(Accuracy=False)

global arg
arg = parser.parse_args()

from tableau20 import tab_cmap, colors
import machineinfo
_all_machines = [ s for (s, _, _) in machineinfo.machines ]
machines = _all_machines if not arg.machines else arg.machines.split()

for m in machines:
    try:

        # Initialize machine to get pairwise send costs
        import config
        from netos_machine import NetosMachine
        from server import SimArgs

        # Set machine name
        config.args = SimArgs()
        config.args.machine = m

        m_class = NetosMachine()

        _name = '%s/%s/multimessage.gz' % (MDB, m)
        print _name
        f = gzip.open(_name, 'r')
        print 'Generating machine', m
        plot_multimesage(m, f, False, True)
    except IOError:
        print 'No multimessage data for machine', m, ' - ignoring'

exit(0)
