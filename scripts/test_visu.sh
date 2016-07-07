#!/bin/bash

SCRIPTDIR=$(dirname $0)
source $SCRIPTDIR/common.sh

get_model

python ./simulator.py gruyere adaptivetree --visu; RC=$?

if [[ ! -f visu/visu_gruyere_adaptivetree_atomic_broadcast.png ]];
then
    echo "No output file generated, aborting"
    exit 1
fi

exit $RC
