#!/bin/bash

MODEL=model.h
QDIR=$HOME/bf/quorum/usr/quorum/
TMP=`mktemp`
RESULTDIR=~/measurements/atomic_broadcast/
PATTERN="Quorum.*everything done.*exiting"

# check the output
# --------------------------------------------------
function wait_result() {

	m=$1
	i=0

	# one iteration = 2 seconds
	# This should terminate after 5 minutes = 300 seconds = 150 iterations
    while ! grep -q "$PATTERN" $TMP
    do
		sleep 2
		i=$(($i+1))

		if [[ i -ge 150 ]]
		then
			echo "Timeout, restarting machine"
			rackpower -r $m
			i=0
		fi
    done
}

# main
# --------------------------------------------------
# gruyere sbrinz1
for m in ziger1 gruyere sbrinz1 
do
	# ring,cluster,mst,bintree,sequential,badtree
	# cluster mst bintree sequential 
    for t in badtree cluster mst bintree sequential 
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
	ps -p $PID
	rackboot.sh $m # Reboot the machine
	wait_result $m # Wait for result
	kill $PID # Kill console process
	ps -p $PID

	echo "Benchmark terminating"

	# Copy result
	cp -b $TMP $RESULTDIR/${m}_${t}
	rm $TMP
	
	./simulator.py --evaluate-model $m $t
    done
done

exit 0