#!/bin/bash

export OMP_NUM_THREADS=18
export DEVITO_ARCH="gcc"
export DEVITO_MPI="1"
export DEVITO_OPENMP="1"
export DEVITO_LOGGING="DEBUG"
export OMP_PROC_BIND="true"
export OMP_PLACES="cores"
