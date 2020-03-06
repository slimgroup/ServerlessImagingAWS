#!/bin/bash

# Script to run timings for weak scaling. For every batchsize, runs 3 consecutive timings and
# waits 700 s between runs, to give AWS batch sufficient time to shut down all EC2 instances.

BATCHSIZE="128"

for NUMBER in `echo $BATCHSIZE`
do
    for i in {1..1}
    do
        python launch_test.py $NUMBER $i
        sleep 700s
    done
done
