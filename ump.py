import sys
import tempfile
import subprocess

def execute_ump_breakdown():

    build = tempfile.mkdtemp()
    result = tempfile.mkdtemp()

    print result

    subprocess.call(['/home/skaestle/bf/quorum/tools/harness/scalebench.py',
                     '-B', build, 
                     '-m', 'ziger1', 
                     '-t', 'ump_latency', 
                     '/home/skaestle/bf/quorum/', result])
