import numpy as np
import boto3, json, time, datetime
import matplotlib.pyplot as plt


# Timings for gradient computation w/ batch. 
# Make sure, no other batch jobs are currently running or in a batch queue!!

lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
batch_client = boto3.client('batch')

# Get parameters from json file
with open('parameters.json', 'r') as filename:
    parameters = json.load(filename)

# Invoke lambda function
response = lambda_client.invoke(FunctionName='ComputeGradients', LogType='Tail', Payload=json.dumps(parameters))

# Get job metadata
batch_queue = parameters['batch_queue']
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
    time.sleep(10)

# Ensure job finished successfully
for job in array_job['jobSummaryList']:
    assert job['container']['exitCode'] == 0

# Gather timings (absolute times in ms)
print("Get timings")
T = np.zeros(shape=(array_size, 3))
for j in range(array_size):
    T[j, 0] = array_job['jobSummaryList'][j]['createdAt']
    T[j, 1] = array_job['jobSummaryList'][j]['startedAt']
    T[j, 2] = array_job['jobSummaryList'][j]['stoppedAt']

# Save results w/ current datetime stamp
timestamp = datetime.datetime.now()
timestamp = str(timestamp).replace(' ','')  # remove spaces
T.dump('timings_' + timestamp)

