This is a simulator for multicores.

It can be used to Simulate broadcast trees and generate configurations
to be fed into the Barrelfish's Quorum program.

# Machines

In order for the Simulator to find good configurations for distributed
algorithms (such as tree topologies for atomic broadcasts), it needs
to understand what a machine looks like.

## Python class

Most of the ETH machines should be represented by either one of the
classes in this project (such as `gruyere.py`).

This is deprecated, and should probably be replaced by the information
retrieved in the machine hierarchy part.

## Pairwise

Furthermore, pairwise send and receive cost of all combinations of
cores need to be provided for each machine.

To generate pairwise measurements, execute programs
`pairwise_ump_send` and `pairwise_ump_receive` from
`usr/bench/ump_ump_bench_pairwise`, run the output through script
`evaluate_pairwise-latency.py` and store the output in
`measurements/send_machinename`, `measurements/send_machinename`.

## Machine hierarchy

Last, the hierarchy of caches and affinity of cores to them is needed.

This is generated by a script `scripts/coresenum`, which has to be
executed in Linux and the result stored in
`measurements/coresenum_print_machinename`

# Design

## Overlay

## Hybrid models

Hybrid models consist of a message passing and shared memory
instance. Message passing components have an overlay
(overlay.Overlay), that represents the topology to be used for sending
messages (binary tree, MST)

# Generating a model

In order to generate a model, call the Simulator with the desired
topology and machine name.

```./simulator.py gruyere mst```

In order to generate a hybrid model:

```./simulator.py gruyere hybrid_bintree```
