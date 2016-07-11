#!/usr/bin/python
import matplotlib
matplotlib.use('Agg')

import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import brewer2mpl
import plotsetup
import json
import gzip

import helpers

import sys
import os
from extract_ab_bench import parse_simulator_output, parse_log

PRESENTATION=False
SHOW_ADAPTIVE=None # given as argument

fontsize = 19 if not PRESENTATION else 15

import matplotlib
matplotlib.rcParams['figure.figsize'] = 8.0, 4.5
plt.rc('legend',**{'fontsize':fontsize, 'frameon': 'false'})

matplotlib.rcParams.update({'font.size': fontsize, 'xtick.labelsize':fontsize, 'ytick.labelsize':fontsize})

from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)

ymax_d = {
    'sgs-r820-01': 60
}


if not PRESENTATION:
    matplotlib.rc('font', family='sans-serif')
    matplotlib.rc('font', serif='Times')
    matplotlib.rc('text', usetex='true')

MDIR='machinedb/'

def configure_plot(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

label_lookup = {
    'ab': 'a. broadcast',
    'reduction': 'reduction',
    'barriers': 'barrier',
    'agreement': '2PC'
}

def print_res(plotdata, machine):

    global arg

    print
    print helpers.bcolors.HEADER + helpers.bcolors.UNDERLINE + \
        machine + helpers.bcolors.ENDC
    print


    for t in [ 'ab', 'reduction', 'barriers', 'agreement' ]:

        if arg.algorithm and arg.algorithm!=t:
            continue

        print
        print '------------------------------'
        print t
        print '------------------------------'
        print

        val = plotdata[t].items()
        val = sorted(val, key=lambda x: x[1][0])

        best_other = ('n.a.', sys.maxint)
        (baseline, _, _) = plotdata[t][arg.normalize]
        baseline = float(baseline)

        for topo, (m, e, pred) in val:

            if arg.topology_ignore and arg.topology_ignore in topo:
                continue

            fac = -1

            if arg.normalize:
                fac = m/baseline

            if not 'adaptivetree' in topo and m<best_other[1]:
                best_other = (topo, min(best_other[1], m))

            color = helpers.bcolors.OKGREEN if fac>=1.01 else \
                    (helpers.bcolors.FAIL if fac<=0.99 else '')

            s = '%-30s %5d %8.2f %s %8.2f %s' % \
                (topo, m, e, color, fac, helpers.bcolors.ENDC)

            if arg.highlight and topo == arg.highlight:
                print helpers.bcolors.BOLD + s + helpers.bcolors.ENDC
            else:
                print s

        print 'Best other: %30s %8.2f %8.2f' % \
            (best_other[0], best_other[1], best_other[1]/baseline)

#
# Barchart
#
def multi_bar_chart(plotdata, machine):

    output_for_poster = False
    print 'Plotting data', len(plotdata), plotdata

    import sys
    import os
    sys.path.append(os.getenv('HOME') + '/papers/oracle/scripts/')

    print plotdata

    bars = [
        "mst",
        "bintree",
        "cluster",
        "badtree",
        "fibonacci",
        "sequential",
        #"optimal",
    ]

    N = len(plotdata)
    print N
    ind = numpy.arange(N)

    _width = len(bars)+1 if SHOW_ADAPTIVE==True else len(bars)
    width = 1./(_width + 1)

    # Plot the datall
    f = 'ab-bench-%s' % machine

    if SHOW_ADAPTIVE:
        bars += [ "adaptivetree" ]

    else:
        f += 'no_adaptive'

    with PdfPages('%s.pdf' % f) as pdf:

        fig, ax = plt.subplots()
        labels = [ label_lookup.get(label, label) for (label, data) in plotdata ]

        plt.grid(True, 'both', linestyle='-', linewidth=.5, color='0.4') # color=

        if output_for_poster or PRESENTATION:
            from tableau20 import colors
            hs = [ '' for x in range(9) ]

        else:
            colors = brewer2mpl.get_map('PuOr', 'diverging', 9).mpl_colors
            hs = [ '.', '/', '//', None,  '\\', '\\\\', '*', None, 'o' ]

        legends = []
        n = 0 #if SHOW_ADAPTIVE else 1

        # One bar per algorithm
        for b in bars:

            v = []
            yerr = []
            for (algo, l) in plotdata:
                for (topo, vmean, vstderr, est) in l:
                    if (topo==b):
                        if b == "adaptivetree" and False:
                            v.append(0)
                            yerr.append(0)
                        else:
                            v.append(vmean/1000)
                            yerr.append(vstderr/1000)

            if len(v) == N and len(yerr) == N:
                r = ax.bar(ind+(n+0.5)*width, v, width, \
                           color=colors[n], hatch=hs[n], yerr=yerr, \
                           error_kw=dict(ecolor='gray'))
                if b == "adaptivetree":
                    legends.append((r, "anontree"))
                else:
                    legends.append((r, b))
                n+=1
            else:
                print 'NOT Adding bar - does not have the right dimenstion ', \
                    v, yerr

        if not output_for_poster:
#            ax.set_xlabel('Tree topology ' + machine)
            ax.set_ylabel('Execution time [x1000 cycles]')


        ax.set_xticks(ind + n/2.0*width)

        ax.set_ylim(ymin=0)
        if machine in ymax_d:
            ax.set_ylim(ymax=ymax_d[machine])
            ax.text(3.51, 55, "81865", ha='center', rotation=90, fontsize=16)
            ax.text(3.765, 55, "87907", ha='center', rotation=90, fontsize=16)

        ylticks = [int(i) for i in ax.get_yticks()]
        ax.set_yticklabels(map(str, ylticks))

        ax.set_xticklabels(labels) #, rotation=45)
 #       ax.set_yticks([10000, 20000, 30000, 40000, 50000])
#        ax.set_yticklabels(['10', '20','30','40','50']) #, rotation=45)

        configure_plot(ax)
        lgnd_boxes, lgnd_labels = zip(*legends)
        ax.legend( lgnd_boxes, lgnd_labels, loc=2, ncol=2, borderaxespad=0.,
                  mode="expand",
                  bbox_to_anchor=(0.0, 1.01, .75, .102))

        if output_for_poster:
            print 'Saving picture to', f
            plt.savefig(f + '.png', dpi=1200)
        elif PRESENTATION:
            print 'Saving picture to', f
            plt.savefig(f + '.png', dpi=400, bbox_inches='tight')
        else:
            pdf.savefig(bbox_inches='tight')


def generate_machine(m):

    _raw = MDIR + '%s/ab-bench.gz' % m
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
    print_res(mbench, m)
#    multi_bar_chart(mbench, m)

global arg

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--machines')
parser.add_argument('--showadaptive', dest='showadaptive', action='store_false')
parser.add_argument('--normalize', help='Which measurement should we normalize to?')
parser.add_argument('--highlight', help='Which measurement should be highlighted?')
parser.add_argument('--algorithm', help='Algorithm to evaluate. Default: all')
parser.add_argument('--topology-ignore', help='Topology pattern to ingore. Default: all')
parser.add_argument('-f', dest='force', action='store_true')
parser.set_defaults(showadaptive=True, force=False)
arg = parser.parse_args()

machines = ['gruyere', 'nos4', 'pluton', 'sbrinz1',
            'sgs-r815-03', 'sgs-r820-01', 'tomme1', 'vacherin',
            'ziger2', 'gruyere', 'gottardo' ] \
           if not arg.machines else arg.machines.split()

SHOW_ADAPTIVE = arg.showadaptive

for m in machines:
    try:
        generate_machine(m)
    except IOError as e:
        print 'IOError - probably measurment file does not exist'
    except Exception as e:
        print 'Failed for machine %s' % m
        raise

exit(0)
