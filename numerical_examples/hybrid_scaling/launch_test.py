import numpy as np
import boto3, json, time, datetime, sys
import matplotlib.pyplot as plt
from pytz import timezone
from CloudExtras import array_get

# Timings for gradient computation w/ batch.
# Make sure, no other batch jobs are currently running or in a batch queue!!
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
batch_client = boto3.client('batch')

# Get parameters from json file
with open('parameters.json', 'r') as filename:
    parameters = json.load(filename)

# Check if batchsize is overwritten by environment gradiable from shell script
if len(sys.argv) > 1:
    run_id = str(sys.argv[1])
    multi_socket = str(sys.argv[2])
    omp_num_threads = int(sys.argv[3])
else:
    run_id = 0
    multi_socket = 'FALSE'
    omp_num_threads = 24

# Overwrite job parameters
parameters['multi_socket'] = multi_socket   # RESTRICT, TRUE, FALSE
if multi_socket == 'TRUE':
    parameters['script_name'] = 'bp_synthetic_hybrid.py'
else:
    parameters['script_name'] = 'bp_synthetic_omp.py'
parameters['omp_num_threads'] = omp_num_threads

# Invoke lambda function
if multi_socket == 'TRUE':
    num_cores = 2*parameters['omp_num_threads']
else:
    num_cores = parameters['omp_num_threads']

print("Invoke Lambda function with ", num_cores, " vCPUs, ", omp_num_threads, " OMP_NUM_THREADS, ", parameters['memory']/1e3, " GB RAM and batchsize ", parameters['batchsize'])

response = lambda_client.invoke(FunctionName='ComputeGradients', LogType='Tail', Payload=json.dumps(parameters))

# Get job metadata
batch_queue = parameters['batch_queue']
batchsize = parameters['batchsize']

print("Get job meta data")
while True:
    job = batch_client.list_jobs(jobQueue=batch_queue, jobStatus='RUNNABLE')
    if len(job['jobSummaryList']) == 1:
        break
    job = batch_client.list_jobs(jobQueue=batch_queue, jobStatus='RUNNING')
    if len(job['jobSummaryList']) == 1:
        break
    time.sleep(1)

job_id = job['jobSummaryList'][0]['jobId']
array_size = 1  # single job

# Wait for job to finish
print("Wait for job to finish")
while True:
    job_info = batch_client.describe_jobs(jobs=[job_id])
    array_job = job_info['jobs'][0]
    if array_job['status'] == 'SUCCEEDED':
        break
    time.sleep(10)

# Gather timings (unix time stamps)
print("Get timings")
T = np.zeros(shape=(3))
T[0] = array_job['createdAt']
T[1] = array_job['startedAt']
T[2] = array_job['stoppedAt']

# Get Devito runtimes and script runtimes
key = 'timings_hybrid/hybrid_scaling'
bucket = parameters['bucket_name']
while True:
    try:
        tcont = array_get(bucket, key)
        break
    except:
        time.sleep(1)

T2 = np.zeros(len(tcont))   # should contain 3 values
for j in range(len(T2)):
    T2[j] = tcont[j]

TT = np.concatenate((T, T2), axis=0)    # should be 4 + 3 values: creation, start, stop, gradient_timestamp, kernel time, python_runtime, devito_runtime

# Save results w/ current datetime stamp
timestamp = datetime.datetime.now()
timestamp = str(timestamp).replace(' ','')  # remove spaces
TT.dump('results/timings_hybrid_' + multi_socket + '_num_threads_' + str(omp_num_threads) + '_run_' + str(run_id) + '_' + timestamp)
