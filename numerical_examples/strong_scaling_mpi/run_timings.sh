#!/bin/bash
#NUM_NODES="2 4 8 16 20"
NUM_NODES="2"
NUM_CORES="24"

for NUMBER in `echo $NUM_NODES`
do
    for i in {2..2}
    do
        python launch_test.py $NUMBER $NUM_CORES $i
        echo "Done! Wait for next run."
        sleep 900s
    done
done
