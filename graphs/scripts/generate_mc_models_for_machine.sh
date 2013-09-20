#!/bin/bash

MODEL=model.h
MODEL_DEF=model_defs.h

MAX_CORES=32
NUM_NODES=8
NODE_SIZE=4

# main
# --------------------------------------------------
for m in $@
do
    for t in mst cluster adaptivetree bintree badtree fibonacci
    do

	for i in $(seq 2 $NUM_NODES)
	do
	    echo $i

	    GROUP=$(python -c "print ','.join(map(str, [x for x in range(("$NODE_SIZE"*"$(($i-1))")+1) if x % "$NODE_SIZE" == 0]))")
	    echo $GROUP

            # Cleanup 
	    rm -f $MODEL
	    
	    # Run the simulator
	    ./simulator.py --multicast --group "$GROUP" $m $t || exit 1

            # Copy the model
	    cp $MODEL $MODEL.$t.$i
	    cp $MODEL_DEF $MODEL_DEF.$t.$i

	done

    done
done

find . -regex '.*model.*[0-9]' -regextype posix-egrep -exec cp {} /local/nfs/atomicbroadcast/umpq/ \;

exit 0