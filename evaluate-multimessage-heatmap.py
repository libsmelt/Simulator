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
from tableau20 import tab_cmap, colors

import matplotlib

from config import MACHINE_DATABASE
MDB= '%s/' % MACHINE_DATABASE

sys.path.append(MDB)
import machineinfo

fontsize = 14
mode_list = [ 'sum', 'sumA', 'last', 'all' ]

# CONFIGURE FONT
# --------------------------------------------------

PRESENTATION=False           # << font + colors
OUTPUT_FOR_POSTER=False     # << higher resolution

import matplotlib
matplotlib.rcParams['figure.figsize'] = 8.0, 4.0
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

def do_plot(cores_remote, cores_local, z, mode, machine):
    # PREPARE heat map plot
    # --------------------------------------------------

    # make these smaller to increase the resolution
    dx, dy = 1.0, 1.0 # 0.15, 0.05

    # generate grid for the x & y bounds
    Y, X = np.mgrid[slice(0, cores_remote+1, dy),
                    slice(0, cores_local+1, dx)]

    fig, ax = plt.subplots()

    plt.pcolor(X, Y, z, cmap=tab_cmap) # , vmin=1-z_dist, vmax=1+z_dist)
    cb = plt.colorbar()

    color=cm.rainbow(numpy.linspace(0,1,cores_remote))

    # PRINT MEASUREMENTS
    # --------------------------------------------------

    for x in range(0,cores_local):
        for y in range(0, cores_remote):
            color = 'black'
            plt.text(x + 0.5, y + 0.5, '%.0f' % (z[y][x]),
                     horizontalalignment='center',
                     verticalalignment='center',
                     color=color,
                     fontsize=11)


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


    print "parsing multimessasge for " + machine

    tsc_overhead = 0
    cores_local = 0
    cores_remote = 0
    cores_total = 0

    data = {}
    err = {}

    # PARSE INPUT
    # --------------------------------------------------

    for line in f:
        #             r=0,l=3, mode=sum , avg=140, stdev=11, med=141, min=117, max=156 cycles, count=1800, ignored=3200
        m = re.match('r=(\d+),l=(\d+), mode=([^,]+), avg=(\d+), stdev=(\d+), med=(\d+), min=(\d+), max=(\d+) cycles, count=(\d+), ignored=(\d+)', line)
        if m :
            l = int(m.group(2))
            r = int(m.group(1))
            mode = m.group(3).rstrip()
            print 'found', l, r, mode, int(m.group(4))

            data[mode][r][l] = int(m.group(4))
            err[mode][r][l] = int(m.group(5))

            # # Store depending on type of measurement
            # if int(m.group(3)) == 1 :
            #     data_last[r][l] = int(m.group(4))
            #     err_last[r][l] = int(m.group(5))
            # else :
            #     data_all[r][l] = int(m.group(4))
            #     err_all[r][l] = int(m.group(5))

            #     if l + r == 1: # Only one message sent
            #         _last = 0
            #     else:
            #         if l > 0: # Last message was a local one
            #             _last = data_diff[r][l-1]
            #         else:
            #             _last = data_diff[r-1][l]

            #     data_diff[r][l] = int(m.group(4)) - _last


        m = re.match('Calibrating TSC overhead is (\d+) cycles', line)
        if m:
            print "TSC " + m.group(1)
            tsc_overhead = int(m.group(1))

        m = re.match('num_local_cores=(\d+), num_cluster=(\d+)', line)
        if m:
            cores_local = int(m.group(1))
            cores_remote = int(m.group(2))
            print "num_local_cores " + str(cores_local)
            print "num_cluster " + str(cores_remote)

            for l in mode_list:
                data[l] = [[0 for i in range(cores_local)] for j in range(cores_remote)]
                err[l] = [[0 for i in range(cores_local)] for j in range(cores_remote)]


    for m in mode_list:
        z = np.zeros((cores_remote, cores_local), dtype=np.float)
        for x in range(cores_remote):
            for y in range(cores_local):
                if data[m][x][y] == 0:
                    print 'Warning', m, x, y, 'is 0'
                z[x][y] = data[m][x][y]
        do_plot(cores_remote, cores_local, z, m, machine)



import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--machines')
arg = parser.parse_args()

import machineinfo
_all_machines = [ s for (s, _, _) in machineinfo.machines ]
machines = _all_machines if not arg.machines else arg.machines.split()

for m in machines:
    try:
        _name = '%s/%s/multimessage.gz' % (MDB, m)
        print _name
        f = gzip.open(_name, 'r')
        print 'Generating machine', m
        plot_multimesage(m, f, False, True)
    except IOError:
        print 'No multimessage data for machine', m, ' - ignoring'

exit(0)
