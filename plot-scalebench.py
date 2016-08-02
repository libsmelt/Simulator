#!/usr/bin/python
import matplotlib
matplotlib.use('Agg')

import numpy
import matplotlib.pyplot as plt
import json
from matplotlib.backends.backend_pdf import PdfPages

import brewer2mpl
import plotsetup

import sys
import os
import gzip
import helpers
from extract_ab_bench import parse_simulator_output, parse_log

fontsize = 19

import matplotlib
matplotlib.rcParams['figure.figsize'] = 8.0, 4.5
plt.rc('legend',**{'fontsize':fontsize, 'frameon': 'false'})
matplotlib.rc('font', family='sans-serif')
matplotlib.rc('font', serif='Times')
matplotlib.rc('text', usetex='true')
matplotlib.rcParams.update({'font.size': fontsize, 'xtick.labelsize':fontsize, 'ytick.labelsize':fontsize})

from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)

MDB='machinedb/'
EXPORT_LATEX=True

import debug

def configure_plot(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

label_lookup = {
    'barriers': 'barrier',
}

#
# Barchart
#
import numpy as np
def multi_bar_chart(plotdata, machine, alg):
    output_for_poster = False

    import sys
    import os
    sys.path.append(os.getenv('HOME') + '/papers/oracle/scripts/')

    # Determine all the topologies in the data set
    # The first one is ours, labeled AnonTree
    _, l = plotdata[0]
    topos = list(set([ t.rstrip('0123456789-') for (t, _, _, _) in l ]))
    # Filter out anything containing --topology-ignore
    topos = [ x for x in topos if not arg.topology_ignore in x ]
    # Filter out other adaptive trees
    topos = [ x for x in topos if not 'adaptivetree' in x or x == arg.adaptive_tree ]
    print 'Plotting topos', topos

    N = len(plotdata)
    ind = numpy.arange(N)

    # Plot the datall
    f = '%s/%s/scalebench-%s-%s-%d.pdf' % (MDB, machine, alg, machine, arg.step)

    max_cores = 0

    xticks = []

    mean  = { s: [] for s in topos }
    stdv  = { s: [] for s in topos }
    clst = { s: [] for s in topos }


    print 'Generating plot for rr-step', arg.step

    have_data = False
    fig, ax = plt.subplots();
    for topo in topos:
        for cores in range(0, 100):
            for (algo, l) in plotdata:
                if algo == alg:
                    for (t, vmean, stderr, err) in l:
                        s = '%s%d-%d' % (topo, cores, arg.step)
                        if t == s:
                            mean[topo].append(vmean)
                            stdv[topo].append(stderr)
                            clst[topo].append(cores)
                            have_data = True
                            if not cores in xticks:
                                xticks.append(cores);
                                if cores > max_cores: # Wtf is this?
                                    max_cores = cores;


    assert len(set([ len(mean[t]) for t in topos ]))<=1 # Make sure all topo values have the same dimension
    assert len(set([ len(stdv[t]) for t in topos ]))<=1 # Make sure all topo values have the same dimension


    if not have_data:
        helpers.warn('No data - no plot created')
        return

    print 'Mean', mean
    print 'Std error', stdv

    signs = ['-.x','-.+','-.o','-^']
    signs_pos = 0

    xticks.sort()
    for topo in topos:
        label = topo.replace('adaptivetree', 'at')
        print 'plotting', label, mean[topo]
        xsteps = sorted(set(clst[topo]))
        plt.errorbar(xsteps,
                     mean[topo], yerr=stdv[topo],
                     fmt=signs[signs_pos], label=label)
        signs_pos = (signs_pos + 1) % len(signs)

        if EXPORT_LATEX:
            _f = f + ('_%s.dat' % topo)
            with open(_f, 'w') as fl:
                fl.write('x y e\n')
                for (x,v,e) in zip(xsteps, mean[topo], stdv[topo]):
                    fl.write('%d %f %f\n' % (x, v, e))
                fl.close()


    plt.legend(ncol=2)
    plt.xlabel('Number of cores')
    ax.set_ylabel('Execution time [x1000 cycles]')

    plt.title('Multicast %s - %i step-size' % (machine, arg.step))

    maxi = 0
    for topo in topos:
        if max(mean[topo]) > maxi:
            maxi = max(mean[topo])

    plt.axis([2, max_cores+1, 0, maxi*1.5])

    plt.xticks(np.arange(2, max_cores+1, max_cores/16))
    #plt.title('%s on %s' % (alg, machine.split('_')[0]))

    ylticks = [int(i) for i in ax.get_yticks()]
    ax.set_yticklabels(map(str, ylticks))

    ylticks = [int(i) for i in ax.get_xticks()]
    ax.set_xticklabels(map(str, ylticks))

    print 'Plotting to', f
    with PdfPages(f) as pdf:
        plt.savefig(pdf, format='pdf')


def generate_machine(m):


    _raw = '%s/%s/ab-bench-scale.gz' % (MDB, m)
    _json = _raw + '.json'

    # Try reading from Json file
    try:
        global arg
        if arg.force:
            raise Exception('Ignoring json file - force reload')
        with open(_json, 'r') as f:
            _mbench = json.loads(f.read())
            mbench = _mbench #{ a: { title: (v, e, 0) for (title, v, e, _) in x } for (a, x) in _mbench }
            print 'json summary exists, reading from there .. '
            f.close()
    except:
        print 'json summary does not exist, generating .. from ', _raw

        mbench = parse_log(gzip.open(_raw), True)
        f = open(_json, 'w')
        json.dump(mbench, f)
        f.close()

    import ast

#    multi_bar_chart(mbench, m, 'barriers')
    multi_bar_chart(mbench, m, 'ab')
#    multi_bar_chart(mbench, m, 'reduction')
#    multi_bar_chart(mbench, m, 'agreement')



import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--machines')
parser.add_argument('--no-mbench', dest='mbench', action='store_false')
parser.add_argument('-f', dest='force', action='store_true')
parser.add_argument('--topology-ignore', help='Topology pattern to ingore. Default: naive', default='naive')
parser.add_argument('--adaptive-tree', help='Which version of the adaptive tree should be shown: adaptivetree-nomm-shuffle-sort', default='adaptivetree-nomm-shuffle-sort')
parser.add_argument('--step', type=int, help='Which rr-step should I plot?', default=1)
parser.set_defaults(sim=True, mbench=True, bfcomp=False, force=False)
arg = parser.parse_args()

machines = ['gottardo'] \
           if not arg.machines else arg.machines.split()

do_sim = False
do_mbench = True

from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

for m in machines:
    generate_machine(m)

print "Used step", arg.step

exit(0)
