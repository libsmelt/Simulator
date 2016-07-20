#!/usr/bin/python
import matplotlib
matplotlib.use('Agg')

import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import brewer2mpl
import plotsetup

import sys
import os
import gzip
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

    N = len(plotdata)
    ind = numpy.arange(N)

    # Plot the datall
    f = 'scalebench-%s-%s' % (alg, machine)

  #  topos = ['adaptivetree','cluster','bintree','badtree','mst']
    topos = ['adaptivetree','cluster','bintree','mst']

    max_cores = 0

    steps = []

    mean = { s: [] for s in topos }
    stdv = { s: [] for s in topos }


    with PdfPages('%s.pdf' % f) as pdf:
        fig, ax = plt.subplots();
        for topo in topos:
            for cores in range(0, 100):
                name = '%s%d' %(topo, cores)
                for (algo, l) in plotdata:
                    if algo == alg:
                        for (t, vmean, stderr, err) in l:
                            s = '%s%d' % (topo, cores)
                            if t == s:
                                mean[topo].append(vmean/1000)
                                stdv[topo].append(int(stderr)/1000)
                                if not cores in steps:
                                    steps.append(cores);
                                    if cores > max_cores:
                                        max_cores = cores;

        print(mean)
        print(stdv)

        signs = ['-.x','-.+','-.o','-^']
        signs_pos = 0
        steps.sort()
        for topo in topos:
            if topo == "adaptivetree":
                plt.errorbar(range(2, max_cores+1, 1),
                         mean[topo], yerr=stdv[topo],
                         fmt=signs[signs_pos], label="anontree")
                signs_pos += 1
            else:
                plt.errorbar(range(2, max_cores+1, 1),
                         mean[topo], yerr=stdv[topo],
                         fmt=signs[signs_pos], label=topo)
                signs_pos += 1;

        plt.legend(ncol=2)
        plt.xlabel('Number of cores')
        ax.set_ylabel('Execution time [x1000 cycles]')

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
            mbench = { a: { title: (v, e, 0) for (title, v, e, _) in x } for (a, x) in _mbench }
            print 'json summary exists, reading from there .. '
            f.close()
    except:
        print 'json summary does not exist, generating .. '

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

exit(0)
