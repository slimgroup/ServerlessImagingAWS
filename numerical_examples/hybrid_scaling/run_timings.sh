#!/bin/bash

# Single socket small domain
export MULTI_SOCKET="RESTRICT"
export OMP_NUM_THREADS="24"
for i in {0..2}
do
    python launch_test.py $i $MULTI_SOCKET $OMP_NUM_THREADS
    sleep 10s
done

# Single socket large domain
export MULTI_SOCKET="FALSE"
export OMP_NUM_THREADS="24"
for i in {0..2}
do
    python launch_test.py $i $MULTI_SOCKET $OMP_NUM_THREADS
    sleep 10s
done

# Two sockets large domain OMP only
export MULTI_SOCKET="FALSE"
export OMP_NUM_THREADS="48"
for i in {0..2}
do
    python launch_test.py $i $MULTI_SOCKET $OMP_NUM_THREADS
    sleep 10s
done

# Two sockets large domain OMP + MPI
export MULTI_SOCKET="TRUE"
export OMP_NUM_THREADS="24"
for i in {0..2}
do
    python launch_test.py $i $MULTI_SOCKET $OMP_NUM_THREADS
    sleep 10s
done
