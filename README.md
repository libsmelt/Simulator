This is a simulator for multicores.

[![build status](https://gitlab.inf.ethz.ch/skaestle/Simulator/badges/ci/build.svg)](https://gitlab.inf.ethz.ch/skaestle/Simulator/commits/ci)

It can be used to Simulate broadcast trees and generate configurations
to be fed into the Barrelfish's Quorum program.

# Setup

Install the following packages (on Ubuntu LTS).

    apt-get install python-networkx python-pygraphviz libgv-python python-numpy python-pygraph python-matplotlib

I had to do some manual config to make it work:

    (cd /usr/lib/python2.7/dist-packages; sudo ln -s libgv_python27.x86_64-linux-gnu.so _gv.so)

Then, you have to manually create directories and install the model:

    mkdir graphs/ visu/ model/
    wget 'http://people.inf.ethz.ch/skaestle/machinemodel.gz' -O "machinemodel.gz"
    tar -xzf "machinemodel.gz" -C "model/"


# Machines

In order for the Simulator to find good configurations for distributed
algorithms (such as tree topologies for atomic broadcasts), it needs
to understand what a machine looks like.

Our machine database is based on Gerd's NetOS rack script, that boots
Linux on each rack machine and executes a couple of programs to
determine machine characteristics. There is a script that acquires
that information for each machine that is defined in the database.

We enrich this with a set of low-level benchmarks; currently, this is
only our pairwise UMP send/receive benchmark.

## Static machine information

```lscpu > lscpu.txt```

There is a version of likwid ready to go at `/mnt/scratch/skaestle/software/likwid-likwid-4.0.1/`.
If this does not work out of the box, try recompiling: `make clean && make && make local`.

Ideally, you have to call only:
```(cd /mnt/scratch/skaestle/software/likwid-likwid-4.0.1/; LD_LIBRARY_PATH=.:./ext/lua/:./ext/hwloc/ ./likwid-topology ) > likwid.txt```


## Pairwise

Furthermore, pairwise send and receive cost of all combinations of
cores need to be provided for each machine.

The procedure for generating these is explained in Smelt's repository in README.md


## Machine hierarchy

Last, the hierarchy of caches and affinity of cores to them is needed.

This is now also directly read from the machine database described
above.

# Design

## Overlay

## Hybrid models

Hybrid models consist of a message passing and shared memory
instance. Message passing components have an overlay
(overlay.Overlay), that represents the topology to be used for sending
messages (binary tree, MST)

# Generating Quorum Configurations

This Simulator is used to simulate and configure how messages should
be send by Barrelfish's quorum program at runtime. The simulator
implements several trees and a ring topology.

The Simulator can also generate shared memory models. Currently, it
cannot simulate shared memory models, but it can generate
configuration.

In order to generate a overlays, call the Simulator with the desired
topology and machine name.

```./simulator.py gruyere mst```

In order to generate a hybrid model:

```./simulator.py gruyere hybrid_bintree```

It is also possible to generate several configurations in the same
configuration file. The configuration can then be chanced at runtime
from within the quorum program. This does not just speed up
benchmarking due to fewer machine reboots, but could also be useful
for reconfigurable hardware. An example is:

```./simulator.py gruyere shm hybrid_bintree bintree adaptivetree cluster```


# Run the Simulator as a service

```while [[ 1 ]]; do ./simulator.py --server; sleep 2; done```

Note: If the Simulator is running as a service within the ETH network,
access from the outside world (`pluton`) and the Barrelfish rack cannot
directly access it. Instead, on these machines, you have to setup a
SSH tunnel to `emmentaler`.

This is how you setup the tunnel (directly on the machine where you
want to execute Smelt).

```ssh -L 25041:sgv-skaestle-01:25041 skaestle@10.110.4.4 -p8006 -N```

`10.110.4.4` here is the local IP address of emmentaler as seen from
within the Barrelfish rack. From the outside world, use
`emmentaler1.ethz.ch` instead.

In order for this to work, `export SMLT_HOSTNAME=localhost`.
