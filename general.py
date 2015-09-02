# Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.

import re
import os
import subprocess

from datetime import datetime

# http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def _wiki_single_output_table_header(f):
    f.write("|| '''topology''' || '''time [cycles]''' || '''factor''' || '''stderr''' ||\n")


def _wiki_single_output_table_footer(f, label="Fixme", caption="Fixme"):
    f.write("||<-4 : style=\"border:none;\"> Figure: %s||\n" % caption)

def _wiki_single_output_table_row(f, value, vmin=0):
    """
    @param values: List of tuples (label, measurement, stderr)

    """
    (label, measurement, err) = value
    fac = -1 if vmin == 0 else measurement/vmin

    field = "<#99CCFF )>%.3f" % fac if fac == 1.0 else "<)>%.3f" % fac

    f.write("|| '''%s''' ||<)> %.2f ||%s ||<)> %.2f ||\n" %
            (label, measurement, field, err))


def wiki_single_output_table(f, values):
    """
    @param values: List of tuples (label, measurement, stderr)

    """
    _wiki_single_output_table_header(f)
    vmin = min([ float(m) for (l, m, e) in values ])
    map(lambda x: _wiki_single_output_table_row(f, x, vmin), values)
    _wiki_single_output_table_footer(f)


def _pgf_header(f, caption='TODO', label='TODO'):
    s = (("\\begin{figure}\n"
          "  \\caption{%s}\n"
          "  \\label{%s}\n"
          "  \\begin{tikzpicture}[scale=.75]\n")
         % (caption, label))
    f.write(s)


def _pgf_plot_header(f, plotname, caption, xlabel, ylabel, attr=[], desc='...'):
    label = "pgfplot:%s" % plotname
    s = (("Figure~\\ref{%s} shows %s\n"
          "\\pgfplotsset{width=\linewidth}\n") % (label, desc))
    if xlabel:
        attr.append('xlabel={%s}' % xlabel)
    if ylabel:
        attr.append('ylabel={%s}' % ylabel)
    t = ("    \\begin{axis}[%s]\n") % (','.join(attr))
    f.write(s)
    _pgf_header(f, caption, label)
    f.write(t)


def _pgf_plot_footer(f):
    f.write("    \\end{axis}\n")
    _pgf_footer(f)


def _pgf_footer(f):
    s = ("  \\end{tikzpicture}\n"
         "\\end{figure}\n")
    f.write(s)

def do_pgf_plot(f, data, caption='', xlabel='', ylabel=''):
    """
    """
    do_pgf_several_plots(f, [(None, data)], caption, xlabel, ylabel)

def do_pgf_several_plots(f, ldata, caption='', xlabel='', ylabel=''):
    """
    Generate PGF plot code for the given data
    @param f File to write the code to
    @param data Data points to print as list of tuples (x, y, err)
    """
    now = datetime.today()
    plotname = "%02d%02d%02d" % (now.year, now.month, now.day)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel, attr=
                     [("legend style={"
                       "at={(0,1)},"
                       "anchor=north west}")])

    labels = []

    for (label, data) in ldata:

        if label:
            labels.append(label)
        else:
            labels.append("")

        f.write(("    \\addplot+[\n"
                 "        error bars/y dir=both,\n"
                 "        error bars/y explicit\n"
                 "        ] coordinates {\n"))

        for d in data:
            if d[2] < d[1]: # Drop data if error is too high
                f.write("      (%d,%f) +- (%f,%f)\n" % (d[0], d[1], d[2], d[2]))

        f.write("    };\n");


    if (len(labels)>0):
        f.write("\legend{%s}\n" % ','.join(labels))

    _pgf_plot_footer(f)


def do_pgf_3d_plot(f, datafile, caption='', xlabel=None, ylabel=None, zlabel=None):
    """
    Generate PGF plot code for the given data
    @param f File to write the code to
    @param data Data points to print as list of tuples (x, y, err)

    """
    attr = ['scaled z ticks=false',
            'zmin=0',
            'z tick label style={/pgf/number format/fixed}']
    if zlabel:
        attr.append('zlabel={%s}' % zlabel)
    now = datetime.today()
    plotname = "%02d%02d%02d" % (now.year, now.month, now.day)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel, attr)
    f.write(("    \\addplot3[surf] file {%s};\n") % datafile)
    _pgf_plot_footer(f)


def do_pgf_multi_plot(f, multidata, caption='FIXME', xlabel='FIXME', ylabel='FIXME'):
    """
    Same as do_pgf_multi_plot
    @param list of (label, [(x,y,err)])

    """
    now = datetime.today()
    plotname = "%02d%02d%02d" % (now.year, now.month, now.day)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel,
                     attr=['ybar interval=.3'])

    machines = []
    topos = []
    data = []

    for (legentry, rawdata) in multidata:

        idata = []
        topos = []
        for d in rawdata:
            topos.append(d[0])
            idata.append(d[1])

        data.append(idata)

        machines.append(legentry)

    # "Invert" two dimensional list
    data_new = [[0 for i in range(len(data))] for j in range(len(data[0]))]
    for y in range(len(data[0])):
        for x in range(len(data)):
            tmp = data[x][y]
            data_new[y][x] = tmp

    for idata in data_new:
         f.write(("    \\addplot coordinates {\n"))
         i = 0
         for d in idata:
             f.write("      (%d,%f)\n" % (i, d))
             i += 1
         f.write("    };\n");

    f.write("\legend{%s}\n" % ','.join(topos))

    _pgf_plot_footer(f)



def _latex_header(f, args=[]):
    header = (
        "\\documentclass[a4wide]{article}\n"
        "\\usepackage{url,color,xspace,verbatim,subfig,ctable,multirow,listings}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage{txfonts}\n"
        "\\usepackage{rotating}\n"
        "\\usepackage{paralist}\n"
        "\\usepackage{subfig}\n"
        "\\usepackage{graphics}\n"
        "\\usepackage{enumitem}\n"
        "\\usepackage{times}\n"
        "\\usepackage{amssymb}\n"
        "\\usepackage[colorlinks=true]{hyperref}\n"
        "\\usepackage[ruled,vlined]{algorithm2e}\n"
        "\n"
        "\\graphicspath{{figs/}}\n"
        "\\urlstyle{sf}\n"
        "\n"
        "\\usepackage{tikz}\n"
        "\\usepackage{pgfplots}\n"
        "\\usetikzlibrary{shapes,positioning,calc,snakes,arrows,shapes,fit,backgrounds}\n"
        "\n"
        "%s\n"
        "\\begin{document}\n"
        "\n"
        ) % '\n'.join(args)
    f.write(header)

def _latex_footer(f):
    footer = (
        "\n"
        "\\end{document}\n"
        )
    f.write(footer)

def do_pgf_stacked_plot(f, tuple_data, caption='', xlabel='', ylabel='', desc='...'):
    """
    Generate PGF plot code for the given data
    @param f File to write the code to
    @param data Data points to print as list of tuples (x, y, err)
    """
    now = datetime.today()
    plotname = "%02d%02d%02d%02d%02d" % (now.year, now.month, now.day, now.hour, now.minute)
    _pgf_plot_header(f, plotname, caption, xlabel, ylabel,
                     [ 'ybar stacked', 'ymin=0',
                       ('legend style={'
                        ' at={(0.5,-0.20)},'
                        ' anchor=north,'
                        ' legend columns=-1'
                        '}') ], desc)

    labels = []
    for (l,data) in tuple_data:
        # Header
        f.write(("    \\addplot coordinates {\n"))
        # Data
        for d in data:
            f.write("      (%d,%f)\n" % (d[0], d[1]))
        # Footer
        f.write("    };\n");
        labels.append(l)

    f.write("     \\legend{%s}\n" % ', '.join(labels))
    _pgf_plot_footer(f)


def run_pdflatex(fname, openFile=True):
    """
    Don't forget to flush the file you wrote or close it before calling this

    """
    d = os.path.dirname(fname)
    print d
    if d=='/tmp':
        subprocess.call('rm -rf /tmp/*figure*.pdf', shell=True)
    print 'run_pdflatex in %s' % d
    if subprocess.call(['pdflatex',
                     '-output-directory', d,
                     '-interaction', 'nonstopmode', '-shell-escape',
                        fname], cwd=d) == 0:
        if openFile:
            subprocess.call(['okular', fname.replace('.tex', '.pdf')])

