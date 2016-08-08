#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import simulator
import random
import string
import os
import subprocess

f = open('visall.tex', 'w+')

def w(s):
    f.write(s)

def command(command, argument=None):
    if argument is None:
        return '\\%s' % (command)        
    else:
        return '\\%s{%s}' % (command, argument)

def section(title, level=1):
    d = { 1: 'section', 2: 'subsection' }
    return command(d[level], title) + '\n\n'

def tikz(content,options=[]):
    return (
        '\\begin{tikzpicture}[%s]\n'
        '%s\n'
        '\\end{tikzpicture}\n') % (','.join(options), content)

def figure(content, caption='', 
           ref=''.join(random.sample(string.ascii_letters*6,6))):
    if not ref.startswith('fig:'):
        ref = 'fig:%s' % ref
    return (
        '\\begin{figure}[ht!]\n'
        '%s\n'
        '\\caption{%s}\n'
        '\\label{%s}\n'
        '\\end{figure}\n'
        ) % (content, caption, ref)

def append_to_report():
    for m in simulator.machines:
        m = ''.join([i for i in m if not i.isdigit()])
        w(command('newpage'))
        w(command('clearpage'))
        w(section(m))
        for t in simulator.topologies:
            tex = 'visu/visu_%s_%s' % (m, t)
            if os.path.exists(tex + '.tex'):
                w(section(t, 2))
                opt = [ 'transform shape' ]
                w(figure(tikz('\\input{graphs/%s}' % tex, opt), 
                         'Atomic broadcast on %s using %s topology' % (m, t),
                         'ab_%s_%s' % (m, t)))
                w(command('clearpage'))

def run_all_simulations():
    for m in simulator.machines:
        for t in simulator.topologies:
            if t != 'ring' and m != 'appenzeller':
                res = subprocess.call(['./simulator.py', m, t])
                assert res == 0

# --------------------------------------------------

run_all_simulations()
append_to_report()

