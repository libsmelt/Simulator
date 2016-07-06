#!/bin/bash

function error() {
	echo $1
	exit 1
}


SCRIPTDIR=$(dirname $0)
source $SCRIPTDIR/common.sh

get_model

TOPOS="adaptivetree adaptivetree-mm adaptivetree-mm-shuffle adaptivetree-mm-shuffle-sort mst bintree cluster badtree fibonacci sequential"

# Execute simulator for each topology, indicate error in case of fail
for t in $TOPOS
do
    ./simulator.py gruyere $t || error "Failed for topo $t"
done

# Everything fine, indicate success
exit 0
