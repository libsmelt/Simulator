#!/bin/bash

function error() {
	echo $1
	exit 1
}

function usage() {

    me=`basename "$BASH_SOURCE"`
    echo "Usage: $me"
    exit 1
}

#[[ -n "$1" ]] || usage

RDIR='machinedb/'

if [ -z "$(cd machinedb/ && git status --porcelain | grep -v '\?\?')" ]; then
    echo "Working directory is clean"
else
    error "Please commit working directory first"
fi

BENCHMARKS='multimessage ab-bench pairwise ab-bench-scale colbench epcc barbench barrier-throughput streamcluster'

if [[ -n "$1" ]]; then
    BENCHMARKS=$1
fi

for m in $SKMACHINES
do
    for b in $BENCHMARKS
    do
	OUT="${m}/${b}.gz"
	IN="emmentaler.ethz.ch:projects/bench-sg-rack/results/${b}_${m}.gz"

	(
	    cd machinedb/

	    TMP=$(mktemp)
	    sha1sum "$OUT" 2>/dev/null > $TMP

	    rsync -a "$IN" "$OUT" 2> /dev/null; RC=$?
	    if [[ $RC -ne 0 || ! -f "$OUT" ]]
	    then
		echo "Failed to copy $IN - does not exist on remote"
	    else

		if ! sha1sum "$OUT" 2>&1 | diff -q $TMP - >/dev/null; then

		    echo -e "\033[31mFile $OUT updated\033[m"
		    # git add $OUT
	    fi
	    fi
	)
    done
done

#(cd machinedb/ && git status --untracked-files=no)
