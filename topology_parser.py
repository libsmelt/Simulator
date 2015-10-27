from string import lstrip
import re
import os
import config

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
            self.add_cluster(self.cluster) # untested
        self.cluster = []

    def add_cluster(self, cluster):
        """Add a single cluster to the list of avialable clusters"""
        self.all.append(map(int, cluster))
        
    def add_clusters(self, clusters):
        """Add the cluster given by as a list of lists, where each inner list
        represents a cluster.

        """
        for c in clusters:
            c_ = c.replace('(', '').replace(')', '')
            self.add_cluster(''.join(c_).split())
        
    def add_core(self, core):
        self.cluster.append(core)

    def pr(self):
        print '%s: %s' % (self.name, str(self.all))

    def get(self):
        return self.all


   
def parse_machine_db(machine):
    '''Returns a dictionary of lists of lists with cores sharing the same
    instance of the resource indicated by the dictionary key
    '''

    res = { s: Resource(s) for s in resources }
    curr_res = None # Current resource

    stream = open('%s/%s/likwid.txt' % (config.MACHINE_DATABASE, machine))
    for l in stream.readlines():

        # Find sockets
        m = re.match('Socket (\d+): \(([0-9 ]*)\)', l)
        if m:
            res['Package'].add_cluster(m.group(2).split())

        # Find cache, remember level
        m = re.match('Level:\s+(\d)', l)
        if m:
            curr_res = 'Cache level %s' % m.group(1)

        # Find cache groups
        m = re.match('Cache groups:(.*)', l)
        if m:
            res[curr_res].add_clusters(m.group(1).split(') ('))

    stream.close()
    stream = open('%s/%s/lscpu.txt' % (config.MACHINE_DATABASE, machine))

    for l in stream.readlines():

        # Find NUMA node
        m = re.match('^NUMA node\d+ CPU\(s\):\s+([0-9,]*)', l)
        if m:
            c = m.group(1).split(',')
            res['NUMA'].add_cluster(c)
            
    for r in res.values():
        r.pr()

            
    return res

