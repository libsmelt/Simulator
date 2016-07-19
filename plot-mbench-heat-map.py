#!/usr/bin/python
import matplotlib
matplotlib.use('Agg')

import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_pdf import PdfPages


import brewer2mpl
import plotsetup
import json

import numpy as np
import sys
import os

import matplotlib.cm as cm

NETOSDB=os.getenv('HOME') + '/Phd/projects/netos-machine-hardware-information/'
sys.path.append(os.getenv('HOME') + '/bin')
sys.path.append(os.getenv('HOME') + '/projects/smelt/scripts/')
sys.path.append(os.getenv('HOME') + '/projects/Simulator/')
sys.path.append(NETOSDB)

#import generatelatex

# sys.path.append(os.getenv('HOME') + '/bin')
# import debug

from extract_ab_bench import parse_simulator_output, parse_log
#import generatelatex

PRESENTATION=False
MAX_Z_DIFF=.4 # Maximum range for colorbar (1.0 - MAX_Z_DIFF, 1.0 + MAX_Z_DIFF)

# Dict storing number of cores per machine - for reordering machines
num_cores = {
    "nos4": 4,
    "sbrinz1": 15,
    "gruyere": 31,
    "gottardo": 32,
    "ziger2": 24,
#    "vacherin": 4,
    "sgs-r820-01": 64,
#    "pluton": 33,
#    "sgs-r815-03": 34,
    "tomme1": 17,
    "appenzeller": 48,
    "babybel1": 20
}
# appenzeller babybel1 gottardo gruyere nos4
# sbrinz1 sgs-r815-03 sgs-r820-01 tomme1 ziger2
import debug

translate = {
    "nos4": "A SR 2x2x1",
    "gottardo": "I NL 4x8x1",
    "gruyere": "A BC 8x4x1",
    "sbrinz1": "A SH 4x4x1",
#    "sgs-r815-03": "A IL 4x4x2",
    "sgs-r820-01": "I SB 4x8x2",
    "tomme1": "I BF 2x4x2",
    "vacherin": "I HW 1x4x1",
    "ziger2": "A IS 4x6x1",
#    "pluton": "I SB 2x8x2",
    "appenzeller": "A MC 4x12x1",
    "babybel1": "I NA 2x10x1"
}

# Assign a x-axis position for each machine, based on sorted num_cores array
num_cores_ordered = { machine: idx for ((machine, numcores), idx) in \
                      zip(sorted(num_cores.items(), key=lambda x: x[1]), \
                          range(len(num_cores))) }

fontsize = 12

import matplotlib
plt.rc('legend',**{'fontsize':fontsize, 'frameon': 'false'})
matplotlib.rc('font', family='serif')
matplotlib.rc('font', serif='Times New Roman')
matplotlib.rc('text', usetex='true')
matplotlib.rcParams.update({'font.size': fontsize, 'xtick.labelsize':fontsize, 'ytick.labelsize':fontsize})

def machine_name_translation(_in):

    print 'Looking up', _in
    val = translate[_in]
    assert val
    return val


matplotlib.rcParams['figure.figsize'] = 8.0, 3.5

# Directory from which to read the measurements
MDIR='machinedb/'

def configure_plot(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

label_lookup = {
    'ab': 'a. broadc.',
    'barriers': 'barrier',
    'agreement': '2PC'
}

from tableau20 import tab_cmap, colors, tab2_cmap
ADAPTIVE=None # set by arg

#
# Heat map
#
def heatmap(data, args):

    with PdfPages('ab-heatmap-%s.pdf' % ('worst' if args.worst else 'best')) as pdf:

        num_machines = len(data)
        print 'Number of machines', num_machines

        num_algorithms = len(data.items()[0][1])
        print 'Number of algirthms', num_algorithms

        # make these smaller to increase the resolution
        dx, dy = 1.0, 1.0 # 0.15, 0.05

        # generate grid for the x & y bounds
        Y, X = np.mgrid[slice(0, num_algorithms+1, dy),
                        slice(0, num_machines+1, dx)]

        z = np.zeros((num_algorithms, num_machines), dtype=np.float)

        machines = [ None for i in range(num_machines) ]
        algorithms = [ None for i in range(num_algorithms) ]

        x = 0
        for machine_org, results in data.items():

            machine = machine_name_translation(machine_org)

            y = 0

            assert machine_org in num_cores_ordered
            _x = num_cores_ordered[machine_org]

            machines[_x] = machine

            for _results in results:

                (label, data) = _results

                # Update the y-axis label according to label_lookup array
                label = label_lookup.get(label, label)

                print label
                if x == 0:
                    algorithms[y] = label
                else:
                    assert algorithms[y] == label # otherwise different order

                _min = sys.maxint
                _max = -1
                adaptive = None

                # Pass over topologies
                for d in  data:
                    print d
                    (topo, val, err, _) = d

                    if topo == ADAPTIVE:
                        adaptive = val
                    else:
                        # Ignore 'naive' measurements, inogre other 'adapative'
                        if 'adaptive' in topo or 'naive' in topo:
                            continue
                        else:
                            _min = min(_min, val)
                            _max = max(_max, val)

                if args.worst:
                    fac = (float(adaptive)/_max)
                else:
                    fac = (_min/float(adaptive))

                print 'Adaptive:', adaptive
                print 'Min:', _min
                print 'Max:', _max
                print 'Factor:', fac

                z[y,_x] = fac
                print 'Setting %d/%d to %f' % (_x,y,fac)
                y += 1

            x += 1

        # x and y are bounds, so z should be the value *inside* those bounds.
        # Therefore, remove the last value from the z array.
        # z = z[:-1, :-1]

        # Maximum distance from 1.0


        z_min, z_max = np.min(z), np.max(z)
        z_min = abs(1-z_min)
        z_max = abs(1-z_max)
        z_dist = max(z_min, z_max)

        z_dist = min(z_min, MAX_Z_DIFF) # never have a scale bigger than 0.5

        fig, ax = plt.subplots()

        z_dist = MAX_Z_DIFF
        plt.pcolor(X, Y, z, cmap=tab_cmap, vmin=1-z_dist, vmax=1+z_dist)
        cb = plt.colorbar()

        for x in range(0,num_machines):
            for y in range(0, num_algorithms):
                color = 'black'
                plt.text(x + 0.5, y + 0.5, '%.2f' % (z[y][x]),
                        horizontalalignment='center',
                        verticalalignment='center',
                        color=color,
                         fontsize=int(fontsize*0.8))

        for y in range(0, num_algorithms):
            avg = 0.0
            for x in range(num_machines):
                avg += z[y][x]

            print 'Average benefit of using Smelt for %s: %8.2f' % \
                (algorithms[y], float(avg)/num_machines)


        ax.set_xticks([ i + 0.5 for i in range(num_machines)])
        ax.set_xticklabels(machines)

        ax.set_yticks([ i + 0.5 for i in range(num_algorithms)])
        ax.set_yticklabels(algorithms)

        ax.set_xlim(xmin=0,xmax=num_machines)
        ax.set_ylim(ymin=0,ymax=num_algorithms)

        labels = []
        for i in cb.ax.yaxis.get_major_ticks():
            txt = str(i.label1.get_text())
            txt = txt.replace("$", "")
            labels.append(txt)


#        ylticks = [i.label1 for i in cb.ax.yaxis.get_major_ticks()]
        #cb.ax.set_yticklabels(map(str, ylticks))
        cb.ax.set_yticklabels(labels)
        #cb.ax.yaxis.set_major_ticks()
#        cb.ax.yaxis.set_tick_params(which='major', )
    #    ax.set_xlabel('machine')
    #    ax.set_ylabel('algorithm')

        fig.autofmt_xdate() # rotate x-labels
        plt.tight_layout() # re-create bounding-box

        fout = 'ab-heatmap-%s.png' % ('worst' if args.worst else 'best')
        plt.savefig(fout)

        pdf.savefig(bbox_inches='tight')

def generate_machine(m, mbench):
    """Much nicer solution to this in <netosdb>/evaluate-prediction.py

    There, we convert the list of lists to dictionaries:
    out = { a: { title: (v, e, 0) for (title, v, e, _) in x } for (a, x) in _d }
    """

    _raw = MDIR + '%s/ab-bench.gz' % m
    _json = _raw + '.json'

    # Try reading from Json file
    try:
        if arg.regenerate:
            raise Exception('Regenerating')
        with open(_json, 'r') as f:
            _d = json.loads(f.read())
            print 'json summary exists, reading from there .. '
            mbench[m] = _d
            f.close()
    except:
        print 'json summary does not exist, generating .. '

        _d = parse_log(open(_raw), True)
        mbench[m] = _d
        f = open(_json, 'w')
        json.dump(_d, f)
        f.close()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--machines')
parser.add_argument('--worst', help='Compare with worst instead of best',
                    action='store_true', dest='worst')
parser.add_argument('--regenerate', help='Do not used cached data',
                    action='store_true', dest='regenerate')
parser.add_argument('--adaptive', help='Which adaptivetree to choose',
                    default='adaptivetree-nomm-shuffle-sort')
parser.set_defaults(worst=False, regenerate=False)
arg = parser.parse_args()

ADAPTIVE=arg.adaptive

# appenzeller babybel1 gottardo gruyere nos4 sbrinz1 sgs-r815-03
# sgs-r820-01 tomme1 ziger2

machines = ['sbrinz1', 'gruyere', 'babybel1',
            'sgs-r820-01', 'tomme1', 'appenzeller',
            'ziger2', 'gottardo', 'nos4'] \
           if not arg.machines else arg.machines.split()

mbench = {}
for m in machines:
    generate_machine(m, mbench)

print mbench
heatmap(mbench, arg)

exit(0)
