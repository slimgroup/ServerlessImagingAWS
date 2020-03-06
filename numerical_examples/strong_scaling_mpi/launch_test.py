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

# Check if batchsize is overwritten by environment variable from shell script
if len(sys.argv) > 1:
    parameters['num_nodes'] = int(sys.argv[1])
    parameters['num_cores'] = int(sys.argv[2])
    run_id = str(sys.argv[3])

# Get job metadata
batch_queue = parameters['batch_queue']
batchsize = parameters['batchsize']
num_nodes = parameters['num_nodes']

# Invoke lambda function
print("Invoke Lambda function with ", parameters['num_nodes'], " nodes, ", parameters['num_cores'], " vCPUs, ", \
    parameters['memory']/1e3, " GB RAM and instance type: ", parameters['instance_type'])

response = lambda_client.invoke(FunctionName='ComputeGradients_MultiNode', LogType='Tail', Payload=json.dumps(parameters))

print("Get job meta data")
while True:
    job = batch_client.list_jobs(jobQueue=parameters['batch_queue'], jobStatus='RUNNABLE')
    if len(job['jobSummaryList']) == 1:
        break
    time.sleep(1)

job_id = job['jobSummaryList'][0]['jobId']
array_size = 1

# Wait for job to finish
print("Wait for job to finish")
while True:
    array_job = batch_client.list_jobs(arrayJobId=job_id, jobStatus='SUCCEEDED')
    if len(array_job['jobSummaryList']) == array_size:
        break
    time.sleep(10)

# Ensure job finished successfully
for job in array_job['jobSummaryList']:
    assert job['container']['exitCode'] == 0

# Gather timings (unix time stamps)
print("Get timings")
T = np.zeros(shape=(array_size, 7))
for j in range(array_size):
    T[j, 0] = array_job['jobSummaryList'][j]['createdAt']
    T[j, 1] = array_job['jobSummaryList'][j]['startedAt']
    T[j, 2] = array_job['jobSummaryList'][j]['stoppedAt']

# Wait for result and get time stamp
bucket = parameters['bucket_name']
key = parameters['partial_gradient_path'] + 'chunk_1/' + parameters['gradient_name']
while True:
    try:
        grad_file = s3_client.head_object(Bucket=bucket, Key=key)
        break
    except:
        time.sleep(1)
grad_time_stamp = grad_file['LastModified'].astimezone(timezone('US/Eastern'))
grad_unix_time = int(time.mktime(grad_time_stamp.timetuple())*1000)
T[:, 3] = grad_unix_time

# Get Devito runtimes and script runtimes
key = 'timings/mpi_scaling_nodes_' + str(num_nodes)
while True:
    try:
        tcont = array_get(bucket, key)
        break
    except:
        time.sleep(1)

T[:, 4] = tcont[0]  # kernel runtime
T[:, 5] = tcont[1]  # devito runtime
T[:, 6] = tcont[2]  # script runtime

# Save results w/ current datetime stamp
timestamp = datetime.datetime.now()
timestamp = str(timestamp).replace(' ','')  # remove spaces
T.dump('timings_num_nodes_' + str(num_nodes) + '_run_' + str(run_id) + '_' + timestamp)

# Remove result
s3_client.delete_object(Bucket=bucket, Key=parameters['partial_gradient_path'] + 'chunk_1/' + parameters['gradient_name'])
