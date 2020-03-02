import re
import io

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
        self.all.append(cluster)

    def add_clusters(self, clusters):
        """Add the cluster given by as a list of lists, where each inner list
        represents a cluster.

        """
        for c in clusters:
            c_ = c.replace('(', '').replace(')', '')
            self.add_cluster(''.join(c_).split())

    def get(self):
        return self.all


def _parse_line(cpuid, match):
    """Search a line with the content <match>: <value> in the given
    StringIO instance and return <value>

    """
    cpuid.seek(0)
    for l in cpuid.readlines():
        m = re.match('^(%s.*):\s+(.+)' % match, l)
        if m:
            return (m.group(1), m.group(2).rstrip())

    return (None, None)


def on_same_node(res, cpu1, cpu2):
    """Checks if the CPU given as arguments cpu1 and cpu2 are on the same
    NUMA node.

    @param res Resource summary as returned by parse_machine_db

    """
    for n in res['NUMA'].get():
        if cpu1 in n and cpu2 in n:
            return True

    return False


def parse_machine_db(machine, mdb=None):
    '''Returns a dictionary of lists of lists with cores sharing the same
    instance of the resource indicated by the dictionary key
    '''

    if mdb == None:
        mdb = '.'

    res = { s: Resource(s) for s in resources }
    curr_res = None # Current resource

    # likdwid
    # --------------------------------------------------

    stream = open('%s/machine-data/%s/likwid.txt' % (mdb, machine))
    res['CPU'] = 'unknown'

    res['corelist'] = []
    scan_cores = False

    for l in stream.readlines():

        # Find Cores
        m = re.match('HWThread\s+Thread\s+Core\s+Socket', l)
        if m:
            scan_cores = True
            continue

        m = re.match('(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', l)
        if scan_cores and m:
            res['corelist'].append(int(m.group(1)))
        else:
            scan_cores = False

        # Find sockets
        m = re.match('Socket (\d+):\s+\(([0-9 ]*)\)', l)
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

        # Find CPU
        m = re.match('CPU name:\s*(.+)', l)
        if m:
            res['CPU'] = m.group(1)
        m = re.match('CPU type:\s*(.+)', l)
        # don't overwrite information from CPU name, but set in case it's not yet there
        if m:
            if 'unknown' in res['CPU'].lower():
                res['CPU'] = m.group(1)
            res['architecture'] = m.group(1)

        # Find memory
        memory_type = None
        m = re.match('Total memory:\s*([0-9.]+)\s+MB', l)
        if m:
            assert memory_type == None
            memory_type = 1
            res['memory'] = res.get('memory', 0) + float(m.group(1))

        # Memory: 31409 MB free of total 32252.4 MB
        m = re.match('Memory: [0-9.]+ MB free of total ([0-9.]+) MB', l)
        if m:
            assert memory_type == None or memory_type == 2
            memory_type = 2
            res['memory'] = res.get('memory', 0) + float(m.group(1))

    stream.close()

    # lscpu
    # --------------------------------------------------

    stream = open('%s/machine-data/%s/lscpu.txt' % (mdb, machine))
    lscpu = io.StringIO(stream.read())
    stream.close()

    for l in lscpu:

        # Find NUMA node
        m = re.match('^NUMA node\d+ CPU\(s\):\s+([0-9,\-]*)', l)
        if m:
            _cluster = []
            cores = m.group(1)
            for c in cores.split(','):

                if '-' in c:
                    (s, e) = c.split('-')
                    _cluster += range(int(s), int(e)+1)
                else:
                    _cluster.append(int(c))

            print("adding cluster: " + str(_cluster))

            res['NUMA'].add_cluster(_cluster)


    # cpuid
    # --------------------------------------------------

    stream = open('%s/machine-data/%s/cpuid.txt' % (mdb, machine))
    cpuid = io.StringIO(stream.read())
    stream.close()

    for l in cpuid:

        # Find CPU name in case likwid failed
        m = re.search('\s+\(simple synth\)[^\(]*\((.*?)\)', l)
        if m:
            if 'unknown' in res['architecture'].lower():
                res['architecture'] = m.groups()[0]


    # /proc/cpuinfo
    # --------------------------------------------------

    stream = open('%s/machine-data/%s/proc_cpuinfo.txt' % (mdb, machine))
    cpuinfo = io.StringIO(stream.read())
    stream.close()

    res['machine'] = machine
    res['numcpus'] = int(_parse_line(lscpu, 'CPU\(s\)')[1])
    res['cpuspeed'] = float(_parse_line(lscpu, 'CPU MHz')[1])
    res['L1d'] = (_parse_line(lscpu, 'L1d')[1])
    res['L2'] = (_parse_line(lscpu, 'L2')[1])
    res['L3'] = (_parse_line(lscpu, 'L3')[1])
    res['cpuname'] = _parse_line(cpuinfo, 'model name')[1]


    lscpu.seek(0)
    _lscpu = lscpu.read()

    res['cores']   = re.search("Core\\(s\\) per socket:\s*(\d*)", _lscpu).groups()[0]
    res['sockets'] = int(re.search("Socket\\(s\\):\s*(\d*)", _lscpu).groups()[0])
    res['threads'] = re.search("Thread\\(s\\) per core:\s*(\d*)", _lscpu).groups()[0]


    # Fix missing NUMA information (Xeon Phi)
    if len(res['NUMA'].get()) < 1:
        res['NUMA'].add_cluster(res['corelist'])



    return res


def generate_cpu_name(topo_info):
    cpuname = topo_info['cpuname']
    machine = topo_info['machine']
    mdb = '.'
    out = cpuname
    ghz = None
    amd = False
    if 'AMD' in cpuname:
        out = cpuname[cpuname.index('AMD'):].replace('Processor', '')
        amd = True

    elif 'Intel' in cpuname:
        ghz = cpuname[cpuname.index('@'):].strip('@').strip()
        out = cpuname[:cpuname.index('@')].replace('CPU', '')

    # For AMD machines, we don't have the CPU speed, so we add it manually ourselves
    if amd or '0b/01' in out:

        try:
            stream = open('%s/%s/info_manual.txt' % (mdb, machine))
            ghz = _parse_line(stream, 'CPU MHz')[1]
            stream.close()

        except IOError:
            print ('Cannot read manually added cpuinfo for machine %s' % machine)



    for d in [ 'Processor', 'CPU', '(R)', '(tm)' ]:
        out = out.replace(d, '')

    # Xeon Phi
    if '0b/01' in out:
        out = 'Xeon Phi'

    return (' '.join(out.split()), ghz)


def generate_cpu_arch(arch):

    lookup = {
        'AMD Opteron Dual Core Rev F 90nm': 'AMD Santa Rosa'
    }
    arch = arch.replace('processor', '').strip()
    arch = lookup.get(arch, arch)
    out = arch

    for d in [ 'AMD', 'Intel', 'Xeon', 'Core', 'EP', 'EX', 'EN', '/' ]:
        out = out.replace(d, '')

    return ' '.join(out.split())


def parse_cores(topo_info):
    """
    Thread(s) per core:    1
    Core(s) per socket:    4
    Socket(s):             2

    Will return "1x4x2"
    """
    out = "%sx%sx%s" % (topo_info['sockets'], topo_info['cores'], topo_info['threads'])
    return out


def generate_short_name(topo_info, longer=False, add_cpuspeed_to_name=True):
    """Generate short name for given machine.

    topo_info: machine topology information as returned by
        topology_parser.parse_machine

    """
    lookup = {
        'Nehalem': ('NL', None),
        'Barcelona': ('BC', None),
        'Santa Rosa': ('SR', None),
        'Shanghai': ('SH', None),
        'Interlagos': ('IL', None),
        'SandyBridge': ('SB', 'Sandy Bridge'),
        'Bloomfield': ('BF', None),
        'Haswell': ('HW', None),
        'Istanbul': ('IS', None),
        'Magny Cours': ('MC', None),
        'Ivy': ('IB', None),
        'Knights Corner': ('KNC', None),
        'Kabylake' : ("KL", "Kabylake")
    }

    cpuname, mhz = generate_cpu_name(topo_info)
    architecture = generate_cpu_arch(topo_info['architecture'])
    cpuspeed = '' if mhz == None else ' @ ' + mhz
    cores = parse_cores(topo_info)
    if add_cpuspeed_to_name:
        cores += cpuspeed

    out = ''
    if 'Intel' in cpuname or 'phi' in architecture.lower():
        out += 'Intel ' if longer else 'I '
    elif 'AMD' in cpuname:
        out += 'AMD ' if longer else 'A '

    _arch = None
    for key, (desc, desc_long)  in lookup.items():
        desc_long = key if desc_long == None else desc_long
        if key.lower() in architecture.lower():
            _arch = desc_long if longer else desc
    if _arch == None:
        raise Exception("Don't know this machine's architecture: [%s]" % \
                        architecture.lower())

    out += _arch + ' '
    out += cores

    return out
