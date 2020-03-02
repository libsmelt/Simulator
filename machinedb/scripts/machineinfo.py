#!/usr/bin/env python3

import os
from pexpect import pxssh
import argparse

DEFAULT_USERNAME = 'root'
DEFAULT_PASSWORD = None


parser = argparse.ArgumentParser(description='Retrieve information about a NetOS machine and store it on disk.')
parser.add_argument('hostname', type=str, help='Hostname', nargs='?', default=None)
parser.add_argument('username', type=str, help='User', nargs='?', default=DEFAULT_USERNAME)
parser.add_argument('password', type=str, help='Password', nargs='?', default=DEFAULT_PASSWORD)

machines = [
    #('sgd-dalcoi5-19', 'zgerd', DEFAULT_PASSWORD),
    # ('smaug-1', DEFAULT_PASSWORD, DEFAULT_USERNAME),
    # ('smaug-2', DEFAULT_PASSWORD, DEFAULT_USERNAME),
    # ('smaug-3', DEFAULT_PASSWORD, DEFAULT_USERNAME),
    #('pluton', DEFAULT_PASSWORD, DEFAULT_USERNAME),
    #('phi', DEFAULT_PASSWORD, DEFAULT_USERNAME),
    #('skaestle-ThinkPad-X230', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    #('sgs-r815-03', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    #('sgs-r820-01', 'root', DEFAULT_PASSWORD),
    ('nos4', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('nos5', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('babybel2', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('babybel3', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('babybel1', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('babybel4', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('gruyere', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('sbrinz2', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('tomme1', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('ziger1', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('ziger2', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('appenzeller', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('gottardo', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('feta1', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('feta2', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('feta3', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('feta4', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('feta5', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('mozzarella1', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('mozzarella2', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('mozzarella3', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('mozzarella4', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('mozzarella5', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('vacherin', DEFAULT_USERNAME, DEFAULT_PASSWORD),
    ('tilsiter1', DEFAULT_USERNAME, DEFAULT_PASSWORD),
]

install_packages = [
    'setserial',
    'cpuid',
    'cpufrequtils',
    'hdparm',
    'nfs-common',
    'acpica-tools',
    'acpidump'
    'libnuma1',
    'libnuma-dev',
    'libcairo2',
    'libcairo2-dev'
]

SAVE_CMD = 0
SAVE_FILE = 1

commands = [
    # CPU
    ('lscpu', 'lscpu.txt', SAVE_CMD),
    ('lscpu', 'lscpu.txt', SAVE_CMD),
    ('lscpu --parse', 'lscpu_parse.txt', SAVE_CMD),
    ('cat /proc/cpuinfo', 'proc_cpuinfo.txt', SAVE_CMD),
    ('cat /proc/interrupts', 'proc_interrupts.txt', SAVE_CMD),
    ('cpuid', 'cpuid.txt', SAVE_CMD),
    ('cpuid --raw', 'cpuid_raw.txt', SAVE_CMD),
    ('cpufreq-info', 'cpufreq_info.txt', SAVE_CMD),
    ('sudo likwid-topology -g -c', 'likwid.txt', SAVE_CMD),

    # Machine hardware
    ('dmesg|cat', 'dmesg.txt', SAVE_CMD),
    ('sudo dmidecode', 'dmidecode.txt', SAVE_CMD),
    ('sudo biosdecode', 'biosdecode.txt', SAVE_CMD),

    ('sudo lshw', 'lshw.txt', SAVE_CMD),
    ('sudo lshw -businfo', 'lshw_businfo.txt', SAVE_CMD),
    ('sudo lshw -html', 'lshw.html', SAVE_CMD),

    # PCI
    ('lspci -nn', 'lspci.txt', SAVE_CMD),
    ('sudo lspci -vv -nn', 'lspci_verbose.txt', SAVE_CMD),
    ('sudo lspci -vvv -nn -xxxx', 'lspci_extended.txt', SAVE_CMD),

    # Serial ports
    ('sudo setserial -g -a /dev/ttyS[0123]', 'serial.txt', SAVE_CMD),

    # Hard-disks
    ('sudo hdparm -i /dev/sd[abcd]', 'hdparm.txt', SAVE_CMD),

    # ACPI
    ('sudo acpidump', 'acpi.bin', SAVE_CMD),

    # lstopo
    ('sudo ~/hwloc-1.10.1/utils/lstopo/lstopo --output-format pdf --no-legend --whole-system --whole-io > ~/lstopo_all.pdf', 'lstopo_all.pdf', SAVE_FILE),
    ('sudo ~/hwloc-1.10.1/utils/lstopo/lstopo --output-format pdf --no-legend --whole-system --whole-io --no-caches > ~/lstopo_nocache.pdf', 'lstopo_nocache.pdf', SAVE_FILE),
    ('sudo ~/hwloc-1.10.1/utils/lstopo/lstopo --output-format pdf --no-legend --whole-system --no-caches > ~/lstopo_nocache_simpleio.pdf', 'lstopo_nocache_simpleio.pdf', SAVE_FILE),
]

def mount_nfs(s):
    execute_remote_cmd(s, 'sudo mkdir zgerd')
    execute_remote_cmd(s, 'sudo mount 10.110.4.4:/mnt/local/nfs/zgerd zgerd')

def install_likwid(s):
    execute_remote_cmd(s, 'sudo dpkg -i zgerd/likwid-topology_2.0-1_amd64.deb')

def install_hwloc(s):
    execute_remote_cmd(s, 'sudo tar jxvf zgerd/hwloc-1.10.1.tar.bz2')
    execute_remote_cmd(s, 'cd ~/hwloc-1.10.1/ && sudo ./configure')
    execute_remote_cmd(s, 'cd ~/hwloc-1.10.1/ && sudo make')
    execute_remote_cmd(s, 'cd ~/hwloc-1.10.1/ && sudo make install')

def retrieve_file(remote, outfile):
    machine, user, password = remote
    if password != None:
        # Rewrite this function using Paramiko sftp library for example
        # if you want this feature
        assert "Ignore password, we assume SSH key set-up!"
    os.system("scp %s@%s:~/%s %s/%s" % (user, machine, outfile, machine, outfile))

def install_required_packages(s):
    execute_remote_cmd(s, 'sudo add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe"')
    execute_remote_cmd(s, "sudo apt-get -y update")

    for p in install_packages:
        execute_remote_cmd(s, "sudo apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confnew install %s" % p)


def execute_remote_cmd(s, cmd):
    print("Remote executing: %s" % cmd)
    s.try_read_prompt(1.0) # without this, there's a 10% chance of pexpect getting confused
    s.sendline(cmd)
    s.prompt()
    return s.before


if __name__ == '__main__':
    args = parser.parse_args()

    if args.hostname:
        machines = [(args.hostname, args.username, args.password)]

    for machine, user, password in machines:
        if not os.path.exists(machine):
            os.makedirs(machine)

        # Connect to the machine
        s = pxssh.pxssh()
        print("Connecting to machine %s..." % machine)
        s.login(machine, user, password) #, port=8006) # rack machines are running SSH on the default port
        print("Login to %s succeeded" % machine)

        # # Install packages that are not installed by default
        mount_nfs(s)
        #install_required_packages(s)
        install_likwid(s)
        install_hwloc(s)

        # # Find out and save everything about machine
        for cmd, outfile, t in commands:
            output = execute_remote_cmd(s, cmd)
            if t == SAVE_CMD:
                with open(os.path.join(machine, outfile), 'w+') as f:
                    f.write(output)
            elif t == SAVE_FILE:
                retrieve_file((machine, user, password), outfile)

    s.logout()
