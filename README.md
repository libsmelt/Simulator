This is a simulator for multicores.

It can be used to Simulate broadcast trees and generate configurations
to be fed into the Barrelfish's Quorum program.

# Setup

- python-networkx
- python-pygraphviz

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

## Python class

Most of the ETH machines should be represented by either one of the
classes in this project (such as `gruyere.py`).

This is deprecated, and should probably be replaced by the information
retrieved in the machine database.

## Pairwise

Furthermore, pairwise send and receive cost of all combinations of
cores need to be provided for each machine.

The procedure for generating these is explained in the machine
database repository in README.md


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
