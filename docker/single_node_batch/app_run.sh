#!/bin/bash

OMP_NUM_THREADS=${OMP_NUM_THREADS}
echo "Number of threads: $OMP_NUM_THREADS"

# Run devito thread pinning script (disabled by default)
if [ $THREAD_PINNING = "FALSE" ]; then
    echo "No thread pinning."
else
    echo "Use thread pinning."
    ./set_omp_pinning.sh hsw
fi

# Alternatively: enable thread pinning by setting OMP_PLACES
echo "OMP Places: $OMP_PLACES"

# Get script from S3
aws s3 cp s3://${S3_BUCKET}/${SCRIPT_PATH}${SCRIPT_NAME} /app/.    # copy script to /app

# Show available memory on host + container
free -mh
cgget -n --values-only --variable memory.limit_in_bytes /

# Launch app
if [ $MULTI_SOCKET = "TRUE" ]; then
    mpirun --allow-run-as-root -np 2 --map-by socket --report-bindings python3 /app/${SCRIPT_NAME}
else
    python3 /app/${SCRIPT_NAME}
fi
