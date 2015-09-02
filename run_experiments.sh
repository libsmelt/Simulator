#!/bin/bash

MODEL=model.h
MODEL_DEFS=model_defs.h
BFDIR=/mnt/local/skaestle/bf.quorum/
QDIR=$BFDIR/usr/quorum/
TMP=`mktemp`
PATTERN="All experiments done, exiting"
HOSTNAME=emmentaler2.ethz.ch

# --------------------------------------------------

function error() {
	echo $1
	exit 1
}

function usage() {

    echo "Usage: $0 machines [machine..]"
    exit 1
}

[[ -n "$1" ]] || usage

# --------------------------------------------------

function get_result_file()
{
	python <<EOF
import config
print config.get_ab_machine_results('$1', '$2')
EOF
}

# check the output
# --------------------------------------------------
function wait_result() {

	m=$1 # For reboots
	i=0
	j=0

	# one iteration = 2 seconds
	# This should terminate after 5 minutes = 300 seconds = 150 iterations
    while ! grep -q "$PATTERN" $TMP
    do
		sleep 2
		i=$(($i+1))

		# if [[ $i -ge 300 ]]
		# then
		# 	echo "Timeout, restarting machine"
		# 	rackpower -r $m
		# 	i=0
		# 	j=$(($j+1))
		# 	if [[ $j -ge 10 ]]
		# 	then
		# 		echo "Aborting machine restarts after 10 tries"
		# 		exit 1
		# 	fi
		# fi
    done
}

function ctrl_c() {
    echo "** Trapped CTRL-C"
	echo "^c^e." > $FIFO

	sleep 2

    exit 0
}

FIFO=`mktemp`
mkfifo $FIFO
trap ctrl_c INT

# main
# --------------------------------------------------
for m in $@
do
    for t in "shm hybrid_bintree bintree adaptivetree cluster" #mst cluster adaptivetree bintree sequential badtree
    do
	# Cleanup
	rm -f $MODEL $MODEL_DEFS
	echo "" >$TMP

	# Run the simulator
	./simulator.py $m $t || exit 1

	# Quit if generating the model failed
	if [[ ! -e $MODEL ]]
	then
	    echo "The simulator failed to find the model"
	    exit 1
	fi

	# Copy the model
	scp $MODEL emmentaler2.ethz.ch:$QDIR
	scp $MODEL_DEFS emmentaler2.ethz.ch:$QDIR

	# Compile the program
	ssh emmentaler2.ethz.ch /home/skaestle/bin/eth/emntlr_make_generic $BFDIR
	if [ $? -ne 0 ]
	then
	    echo "Compilation failed, exiting"
	    exit 1
	fi

	# Run the machine
	echo "Writing to tmp file: $TMP"
	bfrack console $m >$TMP <$FIFO & # Start console process ..
	PID=$!;	ps -p $PID
	bfrack boot $m # Reboot the machine
	wait_result $m # Wait for result

	echo "Benchmark terminating"

	# # Copy result
	# touch $TMP
	# RESULT=$(get_result_file $m $t)
	# cp -b $TMP ${RESULT}_flounder

	rm $TMP

#	./simulator.py --evaluate-model $m $t

	ctrl_c
    done
done

exit 0
