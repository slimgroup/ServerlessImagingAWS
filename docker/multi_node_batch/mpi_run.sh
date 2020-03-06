#!/bin/bash

# Start SSH
mkdir /var/run/sshd
/usr/sbin/sshd

# Print function and hostfile path
BASENAME="${0##*/}"
log () {
  echo "${BASENAME} - ${1}"
}
HOST_FILE_PATH="/tmp/hostfile"
AWS_BATCH_EXIT_CODE_FILE="/tmp/batch-exit-code"
OMP_NUM_THREADS=${NUM_CORES}
#PYTHONPATH=/app/devito-tti

# Error function
error_exit () {
  log "${BASENAME} - ${1}" >&2
  log "${2:-1}" > $AWS_BATCH_EXIT_CODE_FILE
  kill  $(cat /tmp/supervisord.pid)
}

# Set child by default switch to main if on main node container
NODE_TYPE="child"
if [ "${AWS_BATCH_JOB_MAIN_NODE_INDEX}" == "${AWS_BATCH_JOB_NODE_INDEX}" ]; then
  log "Running synchronize as the main node"
  NODE_TYPE="main"
fi

# wait for all nodes to report
wait_for_nodes () {

  log "Running as master node"
  free -mh
  cgget -n --values-only --variable memory.limit_in_bytes /

  # Add my own ip to hostfile
  touch $HOST_FILE_PATH
  ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)
  log "master details -> $ip"
  echo "$ip" >> $HOST_FILE_PATH

  # Wait for all workers to send their ip to my hostfile
  lines=$(sort $HOST_FILE_PATH|uniq|wc -l)
  while [ "$AWS_BATCH_JOB_NUM_NODES" -gt "$lines" ]
  do
    log "$lines out of $AWS_BATCH_JOB_NUM_NODES nodes joined, check again in 1 second"
    sleep 1
    lines=$(sort $HOST_FILE_PATH|uniq|wc -l)
  done

  # Make the temporary file executable and run it with any given arguments
  log "All nodes successfully joined"

  # Enable thread pinning
  if [ $THREAD_PINNING = "FALSE" ]; then
      echo "No thread pinning."
  else
      echo "Use thread pinning."
      ./set_omp_pinning.sh hsw
  fi

  sleep 1
  log "Run TTI example with MPI"
  log $PYTHONPATH

  # Move script to shared directory and run
  mkdir /efs/scratch/devito
  aws s3 cp s3://${S3_BUCKET}/${SCRIPT_PATH}${SCRIPT_NAME} .    # copy script to /app
  mv /app/$SCRIPT_NAME /efs/scratch/devito/$SCRIPT_NAME # move script to shared directory
  mv /app/send_sqs_msg.py /efs/scratch/devito/send_sqs_msg.py
  mpiexec -n $NUM_NODES --hostfile $HOST_FILE_PATH python3 /efs/scratch/devito/$SCRIPT_NAME
  python3 /efs/scratch/devito/send_sqs_msg.py

  # Clean up, goodbye
  sleep 1
  rm -rf /efs/scratch/devito
  log "done! goodbye, writing exit code to $AWS_BATCH_EXIT_CODE_FILE and shutting down my supervisord"
  echo "0" > $AWS_BATCH_EXIT_CODE_FILE
  exit 0
}

# Fetch and run a script
report_to_master () {

  # Get ip and say hi
  ip=$(/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1)
  log "I am a child node -> $ip, reporting to the master node -> ${AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS}"

  # Display available memory
  free -mh
  cgget -n --values-only --variable memory.limit_in_bytes /

  if [ $THREAD_PINNING = "FALSE" ]; then
      echo "No thread pinning."
  else
      echo "Use thread pinning."
      ./set_omp_pinning.sh hsw
  fi

  # Send ip to master
  until echo "$ip" | ssh ${AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS} "echo ${ip} >> ${HOST_FILE_PATH}"
  do
    echo "Sleeping 2 seconds and trying again"
    sleep 2
  done

  # kill time until master is done
  tail -f /dev/null

  log "done! goodbye"
  exit 0
  }


# Main - dispatch user request to appropriate function
log $NODE_TYPE
case $NODE_TYPE in
  main)
    wait_for_nodes "${@}"
    ;;

  child)
    report_to_master "${@}"
    ;;

  *)
    log $NODE_TYPE
    usage "Could not determine node type. Expected (main/child)"
    ;;
esac
