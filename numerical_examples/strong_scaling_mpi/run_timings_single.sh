#!/bin/bash
NUM_NODES="1"
NUM_CORES="18"

for NUMBER in `echo $NUM_NODES`
do
    for i in {2..2}
    do
        python launch_test_single.py $NUMBER $NUM_CORES $i
        echo "Done! Wait for next run."
        sleep 900s
    done
done
