from string import lstrip
import re

class Resource(object):

    def __init__(self, name):
        self.name = name
        self.a = []
        self.b = []

    def parse(self, element):
        if element.startswith(self.name):
            if self.a:
                self.b.append(self.a)
            self.a = []

    def add_core(self, core):
        self.a.append(core)

    def pr(self):
        print '%s: %s' % (self.name, str(self.b))

def parse_coresenum(stream):

    res = { s: Resource(s) for s in [ 
            'NUMA', 
            'Package',
            'Cache level 3',
            'Cache level 2',
            'Cache level 1', 
            'Cache level 0'] }

    for l in stream.readlines():
        l = l.rstrip()
        elements = l.split('->')
        
        for e in map(lstrip, elements):

            if e.startswith("Core"):
                m = re.match('Core\s\[CPU:\s(\d+)\]', e)
                for r in res.values():
                    r.add_core(m.group(1))
            else:
                for r in res.values():
                    r.parse(e)

    for r in res.values():
        r.pr()

    return res
