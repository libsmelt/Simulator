#!/bin/bash

MACHINEDB='machinedb/'

function download_model() {

    # --------------------------------------------------
    # Download the machine model
    # --------------------------------------------------

    echo " --> downloading model"

    mkdir -p 'visu/' 'graphs/'

    # Clean model directory
    rm -rf $MACHINEDB
    mkdir -p $MACHINEDB

    # Download and install model
    wget 'http://people.inf.ethz.ch/skaestle/machinemodel.gz' -O "machinemodel.gz"
    tar -xzf "machinemodel.gz" -C $MACHINEDB

    ls -R $MACHINEDB
}


function get_model() {

    # --------------------------------------------------
    # Check if the machine model exists. If not, download
    # --------------------------------------------------

    if [[ ! -d $MACHINEDB ]];
    then
	download_model
    else
	echo "Model already downloaded, nothing to do"
    fi
}
