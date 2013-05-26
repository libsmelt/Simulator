#!/bin/bash

MODEL=model.h
QDIR=$HOME/bf/quorum/usr/quorum/
TMP=`mktemp`
RESULTDIR=~/measurements/atomic_broadcast/
PATTERN="Quorum.*everything done.*exiting"

# check the output
# --------------------------------------------------
function wait_result() {

    while ! grep -q "$PATTERN" $TMP
    do
	sleep 2
    done
}

# main
# --------------------------------------------------
for m in gruyere
do
    for t in sequential
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
	    exit 1
	fi

	# Copy the model
	cp $MODEL $QDIR

	# Compile the program
	ssh emmentaler2.ethz.ch emntlr_make_generic /local/skaestle/bf.quorum
	if [ $? -ne 0 ]
	then
	    echo "Compilation failed, exiting"
	    exit 1
	fi

	# Run the machine
	console $m >$TMP & # Start console process .. 
	PID=$! # .. and get PID
	rackboot.sh $m # Reboot the machine
	wait_result # Wait for result
	kill $PID # Kill console process

	echo "Benchmark terminating"

	# Copy result
	cp -b $TMP $RESULTDIR/${m}_${t}
	
	./simulator.py --evaluate $m $t
    done
done

exit 0