from string import lstrip
import re
import os
import config
import StringIO

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

    
def _parse_line(cpuid, match):
    """Search a line with the content <match>: <value> in the given
    StringIO instance and return <value>

    """
    cpuid.seek(0)
    for l in cpuid.readlines():
        m = re.match('^(%s.*):\s+(\S+)' % match, l)
        if m:
            return (m.group(1), m.group(2))

    return (None, None)


def parse_machine_db(machine):
    '''Returns a dictionary of lists of lists with cores sharing the same
    instance of the resource indicated by the dictionary key
    '''

    res = { s: Resource(s) for s in resources }
    curr_res = None # Current resource

    stream = open('%s/%s/likwid.txt' % (config.MACHINE_DATABASE, machine))

    for l in stream.readlines():

        # Find sockets
        m = re.match('Socket (\d+):\s+\(([0-9 ]*)\)', l)
        if m:
            print 'Found cluster'
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
    lscpu = StringIO.StringIO(stream.read())
    stream.close()

    for l in lscpu:

        # Find NUMA node
        m = re.match('^NUMA node\d+ CPU\(s\):\s+([0-9,\-]*)', l)
        if m:
            _cluster = []
            cores = m.group(1)
            print cores
            for c in cores.split(','):
                
                if '-' in c:
                    (s, e) = c.split('-')
                    _cluster += range(int(s), int(e)+1)
                else:
                    _cluster.append(c)

            print _cluster
            res['NUMA'].add_cluster(_cluster)
            
    for r in res.values():
        r.pr()

    res['numcpus'] = int(_parse_line(lscpu, 'CPU\(s\)')[1])
            
    return res

