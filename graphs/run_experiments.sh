#!/bin/bash

MODEL=model.h
QDIR=$HOME/bf/quorum/usr/quorum/
TMP=`mktemp`
RESULTDIR=~/measurements/atomic_broadcast/

# check the output
# --------------------------------------------------
function wait_result() {

    while [[ ! grep "workload_thread terminating" $TMP x]]
    do
	sleep 2
    done
}

# main
# --------------------------------------------------
for m in gruyere
do
    for t in cluster
    do
	# Cleanup 
	rm -f $MODEL
	echo "" >$TMP
	
	# Run the simulator
	./simulator.py $m $t

	# Quit if generating the model failed
	if [[ ! -e $MODEL ]]
	then
	    echo "The simulator failed to find the model"
	    return 1
	fi

	# Copy the model
	cp $MODEL $QDIR

	# Compile the program
	ssh emmentaler2.ethz.ch emntlr_make_generic /local/skaestle/bf.quorum

	# Run the machine
	console $m >$TMP & ;; PID=$! # Start console process and get PID
	rackboot.sh -c $m # Reboot the machine
	wait_result() # Wait for result

	# Copy result
	cp -b $TMP $RESULTDIR/${m}_${t}-`date +%Y%m%d%H%I%S`
    done
done

return 0