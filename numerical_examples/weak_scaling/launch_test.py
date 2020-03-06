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
    parameters['batchsize'] = int(sys.argv[1])
    run_id = str(sys.argv[2])

# Invoke lambda function
print("Invoke Lambda function with batchsize: ", parameters['batchsize'])
response = lambda_client.invoke(FunctionName='ComputeGradients', LogType='Tail', Payload=json.dumps(parameters))

# Get job metadata
batch_queue = parameters['batch_queue']
batchsize = parameters['batchsize']

if batchsize > 1:
    print("Get job meta data")
    while True:
        job = batch_client.list_jobs(jobQueue=batch_queue, jobStatus='PENDING')
        if len(job['jobSummaryList']) == 1:
            break
        time.sleep(1)
    job_id = job['jobSummaryList'][0]['jobId']
    array_size = job['jobSummaryList'][0]['arrayProperties']['size']

    # Wait for job to finish
    print("Wait for job to finish")
    while True:
        array_job = batch_client.list_jobs(arrayJobId=job_id, jobStatus='SUCCEEDED')
        if len(array_job['jobSummaryList']) == array_size:
            break
        time.sleep(1)

    # Ensure job finished successfully
    for job in array_job['jobSummaryList']:
        assert job['container']['exitCode'] == 0

    # Gather timings (unix time stamps)
    print("Get timings")
    T = np.zeros(shape=(array_size, 4))
    for j in range(array_size):
        T[j, 0] = array_job['jobSummaryList'][j]['createdAt']
        T[j, 1] = array_job['jobSummaryList'][j]['startedAt']
        T[j, 2] = array_job['jobSummaryList'][j]['stoppedAt']
else:
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
        time.sleep(1)

    # Gather timings (unix time stamps)
    print("Get timings")
    T = np.zeros(shape=(1, 4))
    T[0, 0] = array_job['createdAt']
    T[0, 1] = array_job['startedAt']
    T[0, 2] = array_job['stoppedAt']

# Wait for result and get time stamp
bucket = parameters['bucket_name']
key = parameters['variable_path'] + 'chunk_1/' + parameters['variable_name'] + \
    str(parameters['iterator']['count'])
while True:
    try:
        var_file = s3_client.head_object(Bucket=bucket, Key=key)
        break
    except:
        time.sleep(1)
var_time_stamp = var_file['LastModified'].astimezone(timezone('US/Eastern'))
var_unix_time = int(time.mktime(var_time_stamp.timetuple())*1000)
T[:, 3] = var_unix_time

# Save results w/ current datetime stamp
timestamp = datetime.datetime.now()
timestamp = str(timestamp).replace(' ','')  # remove spaces
T.dump('timings_batchsize_' + str(batchsize) + '_run_' + str(run_id) + '_' + timestamp)

# Remove variable and full gradients from S3
s3_client.delete_object(Bucket=bucket, Key=parameters['variable_path'] + 'chunk_1/' + parameters['variable_name'] + \
    str(parameters['iterator']['count']))

s3_client.delete_object(Bucket=bucket, Key=parameters['full_gradient_path'] + 'chunk_1/' + parameters['gradient_name'] + \
    str(parameters['iterator']['count']))
