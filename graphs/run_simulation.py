#!/usr/bin/env python

import simulator
import random
import string
import os

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
        '\\begin{figure}[h]\n'
        '%s\n'
        '\\caption{%s}\n'
        '\\label{%s}\n'
        '\\end{figure}\n') % (content, caption, ref)

# --------------------------------------------------

for m in simulator.machines:
    m = ''.join([i for i in m if not i.isdigit()])
    w(section(m))
    for t in simulator.topologies:
        tex = 'visu_%s_%s' % (m, t)
        if os.path.exists(tex + '.tex'):
            command('newpage')
            w(section(t, 2))
            opt = [ 'transform shape', 'scale=.25' ]
#            w(tikz('\\input{graphs/%s}' % tex, opt))
            w(figure(tikz('\\input{graphs/%s}' % tex, opt), 
                     'Atomic broadcast on %s using %s topology' % (m, t),
                     'ab_%s_%s' % (m, t)))
            w(command('clearpage'))
