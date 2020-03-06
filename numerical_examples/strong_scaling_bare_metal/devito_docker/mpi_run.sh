#!/bin/bash

SSHDIR="/home/ubuntu/.ssh"
aws s3 cp s3://slim-bucket-common/pwitte/keys/ssh_host_rsa_key ${SSHDIR}/.
aws s3 cp s3://slim-bucket-common/pwitte/keys/ssh_host_rsa_key.pub ${SSHDIR}/.
cat ${SSHDIR}/ssh_host_rsa_key.pub >> ${SSHDIR}/authorized_keys
echo "Host *" >> ${SSHDIR}/config && echo " StrictHostKeyChecking no" >> ${SSHDIR}/config
sudo chmod 400 ${SSHDIR}/ssh_host_rsa_key ${SSHDIR}/config
eval $(ssh-agent)
ssh-add ~/.ssh/ssh_host_rsa_key

# Environment variables
source environment_variables.sh
NODE_TYPE=$1
AWS_BATCH_JOB_NUM_NODES=$2
HOST_FILE_PATH="/tmp/hostfile"
AWS_BATCH_EXIT_CODE_FILE="/tmp/batch-exit-code"
PYTHONPATH="/home/ubuntu/devito_isotropic"
THREAD_PINNING="FALSE"
S3_BUCKET="slim-bucket-common"
SCRIPT_PATH="pwitte/scripts/"
SCRIPT_NAME="bp_synthetic_mpi_bare_metal.py"

# Print function and hostfile path
BASENAME="$(hostname -I)"
log () {
  echo "${BASENAME}"
}

# Error function
error_exit () {
  log "${BASENAME} - ${1}" >&2
  log "${2:-1}" > $AWS_BATCH_EXIT_CODE_FILE
  kill  $(cat /tmp/supervisord.pid)
}

# wait for all nodes to report
wait_for_nodes () {

  log "Running as master node"

  # Add my own ip to hostfile
  touch $HOST_FILE_PATH
  IP=$(hostname -I)
  log "master details -> $IP"
  echo "$IP" >> $HOST_FILE_PATH
  touch /efs/scratch/master_ip
  echo "$IP" >> /efs/scratch/master_ip

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
  log "Run MPI strong scaling test on bare metal instance."
  log $PYTHONPATH

  # Move script to shared directory and run
  mkdir /efs/scratch/devito
  aws s3 cp s3://${S3_BUCKET}/${SCRIPT_PATH}${SCRIPT_NAME} .    # copy script to home dir
  mv /home/ubuntu/$SCRIPT_NAME /efs/scratch/devito/$SCRIPT_NAME # move script to shared directory

  for i in {0..5}
  do
    mpiexec -n $AWS_BATCH_JOB_NUM_NODES --hostfile $HOST_FILE_PATH python3 /efs/scratch/devito/$SCRIPT_NAME
  done

  # Clean up, goodbye
  sleep 1
  rm -rf /efs/scratch/devito
  rm -rf /efs/scratch/master_ip
  rm -rf $HOST_FILE_PATH
  log "done! goodbye, writing exit code to $AWS_BATCH_EXIT_CODE_FILE and shutting down my supervisord"
  echo "0" > $AWS_BATCH_EXIT_CODE_FILE
  exit 0
}

# Fetch and run a script
report_to_master () {

  # Get ip and say hi
  IP=$(hostname -I)
  AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS=$(cat /efs/scratch/master_ip)
  log "I am a child node -> $IP, reporting to the master node -> ${AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS}"

  if [ $THREAD_PINNING = "FALSE" ]; then
      echo "No thread pinning."
  else
      echo "Use thread pinning."
      ./set_omp_pinning.sh hsw
  fi

  # Send ip to master
  until echo "$IP" | ssh ${AWS_BATCH_JOB_MAIN_NODE_PRIVATE_IPV4_ADDRESS} "echo ${IP} >> ${HOST_FILE_PATH}"
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
