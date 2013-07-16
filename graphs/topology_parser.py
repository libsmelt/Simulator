from string import lstrip
import re

resources = [ 'Cache level 0',
              'Cache level 1',
              'Cache level 2',
              'Cache level 3',
              'Package',
              'NUMA' ]

class Resource(object):

    def __init__(self, name):
        self.name = name
        self.cluster = []
        self.all = []

    def parse(self, element):
        if element.startswith(self.name):
            if self.cluster:
                self.all.append(map(int, self.cluster))
            self.cluster = []

    def finalize(self):
        if self.cluster:
            self.all.append(map(int, self.cluster))
        self.cluster = []

    def add_core(self, core):
        self.cluster.append(core)

    def pr(self):
        print '%s: %s' % (self.name, str(self.all))

    def get(self):
        return self.all

def parse_coresenum(stream):

    res = { s: Resource(s) for s in resources }

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
        r.finalize()
        r.pr()

    return res
