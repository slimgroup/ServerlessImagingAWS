#!/bin/bash

# Environment variables
source environment_variables.sh
PYTHONPATH="/home/ubuntu/devito_isotropic"
THREAD_PINNING="FALSE"
S3_BUCKET="slim-bucket-common"
SCRIPT_PATH="pwitte/scripts/"
SCRIPT_NAME="bp_synthetic_mpi_bare_metal.py"

  # Enable thread pinning
if [ $THREAD_PINNING = "FALSE" ]; then
    echo "No thread pinning."
else
    echo "Use thread pinning."
    ./set_omp_pinning.sh hsw
fi

sleep 1
echo "Run MPI strong scaling test on bare metal instance."

# Move script to shared directory and run
aws s3 cp s3://${S3_BUCKET}/${SCRIPT_PATH}${SCRIPT_NAME} .    # copy script to home dir
for i in {0..9}
do
    python3 $SCRIPT_NAME
done
