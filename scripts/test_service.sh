#!/bin/bash

echo "--------------------------------------------------"
echo "-- Testing Simulator as a service"
echo "--------------------------------------------------"

# PID of the Simulator server
SERVER_PID=0

SCRIPTDIR=$(dirname $0)
F=$SCRIPTDIR/common.sh
echo "sourcing common files $F"
source $F

function terminate() {

    echo "Shutdown requested"
    echo "Dumping Simulator log"
    echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    cat "simulator-server.log"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    kill $SERVER_PID > /dev/null 2>&1;
}

function error() {

    echo $1
    terminate
    echo "Test FAILED"
    sleep 1
    exit 1
}

function ctrl_c() {

    echo "** Trapped CTRL-C .. killing SSH ($PID)"
    terminate
    echo "Test FAILED"
    exit 1
}

function assert_sim_running() {

    # Make sure Simulator is still listening
    (netstat -tulpen | grep 25041); RC=$?
    [[ $RC -eq 0 ]] || error "Simulator is not running"
}

# Get machine model
echo " --> Getting model"
get_model

# Execute Simulator in background
echo " --> Starting Simulator server"
python ./simulator.py --server 2>&1  &
SERVER_PID=$!

# Wait for Simulator to come up
sleep 5

# --------------------------------------------------
# Execute tests
# --------------------------------------------------

assert_sim_running

# Request something from the Simulator
echo " --> Executing tests"
python server-test.py sgs-r815-03 adaptivetree "1,2,3-4,5"; [[ $? -eq 0 ]] || error "Simulator request failed"
assert_sim_running

# --------------------------------------------------
# Execute shutdown
# --------------------------------------------------

echo "All tests passed, attempting shutdown"
terminate
sleep 1

# Make sure Simulator is down
(netstat -tulpen | grep 25041) &>/dev/null; RC=$?;
[[ $RC -ne 0 ]] || error "Simulator is STILL running"

echo "Test PASSED"
exit 0
