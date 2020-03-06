#!/bin/bash

# Socket 1:  0 - 23, 48 - 71
# Socket 2: 24 - 47, 72 - 95

export OMP_NUM_THREADS="1"
export OMP_PLACES='{0}'
for i in {0..2}
do
    python3 bp_synthetic_omp_scaling_bare_metal.py $i
done

export OMP_NUM_THREADS="2"
export OMP_PLACES='{0},{1}'
for i in {0..2}
do
    python3 bp_synthetic_omp_scaling_bare_metal.py $i
done

export OMP_NUM_THREADS="4"
export OMP_PLACES='{0},{1},{2},{3}'
for i in {0..2}
do
    python3 bp_synthetic_omp_scaling_bare_metal.py $i
done

export OMP_NUM_THREADS="8"
export OMP_PLACES='{0},{1},{2},{3},{4},{5},{6},{7}'
for i in {0..2}
do
    python3 bp_synthetic_omp_scaling_bare_metal.py $i
done

export OMP_NUM_THREADS="16"
export OMP_PLACES='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15}'
for i in {0..2}
do
    python3 bp_synthetic_omp_scaling_bare_metal.py $i
done

export OMP_NUM_THREADS="24"
export OMP_PLACES='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23}'
for i in {0..2}
do
    python3 bp_synthetic_omp_scaling_bare_metal.py $i
done
