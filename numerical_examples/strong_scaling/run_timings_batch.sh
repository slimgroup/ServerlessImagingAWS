#!/bin/bash


NUM_CORES="24 16 8 4 2 1"

for NUMBER in `echo $NUM_CORES`
do
    for i in {3..9}
    do
        echo $NUMBER $i
        python launch_test.py $NUMBER $i
    done
done
