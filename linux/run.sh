#!/bin/bash

NUMCORES=`nproc`
echo "Number of processors is $NUMCORES"

for i in `seq 0 $((NUMCORES-1))`
do
	echo "Starting process on core $i"
	taskset -c $i "./latency" &
done

wait
echo "All clients terminated"