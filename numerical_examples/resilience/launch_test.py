import numpy as np
import boto3, json, time, datetime, sys
import matplotlib.pyplot as plt
from pytz import timezone
from CloudExtras import array_get
import subprocess

###############################################################################################
# Auxiliary functions

# Hack, since boto3 has bugs. Therefore use AWS CLI instead
def list_instances_cli(client, state='running'):
    subprocess.call(["./get_timings.sh"])   # write to ec2_instances.txt
    # Read instance ids back in
    fid = open('ec2_instances.txt', 'r')
    id_list = fid.read()
    id_list_split = id_list.split("\"")
    num_ids = int((len(id_list_split)-1)/2)
    instance_ids = []
    for j in range(1, len(id_list_split), 2):
        id = id_list_split[j]
        inst = client.describe_instances(InstanceIds=[id])
        # Check if instance is still running
        if inst['Reservations'][0]['Instances'][0]['State']['Name'] == state:
            instance_ids.append(id_list_split[j])
    # Remove text file w/ IDs
    fid.close()
    subprocess.call(["rm", "-f", "ec2_instances.txt"])
    return instance_ids

def create_failure_schedule(num_instances, failure_rate, schedule):
    # Create schedule to kill instances at random times taken from schedule vector
    # Failure rate is a vector of floats of size >= 1 with values between 0 and 1 (->100 percent)
    num_failures = len(failure_rate)
    K = np.zeros(shape=(num_failures, num_instances))
    for j in range(num_failures):
        num_instances_to_kill = int(num_instances*failure_rate[j])
        idx = np.random.permutation(num_instances)[0:num_instances_to_kill]
        kill_vals = schedule
        K[j, idx] =  kill_vals[0:num_instances_to_kill]
    return K

###############################################################################################

# Timings for gradient computation w/ batch.
# Make sure, no other batch jobs are currently running or in a batch queue!!

lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
batch_client = boto3.client('batch')
ec2_client = boto3.client('ec2')
create_schedule=True

# Get parameters from json file
with open('parameters.json', 'r') as filename:
    parameters = json.load(filename)

# Check if batchsize is overwritten by environment variable from shell script
if len(sys.argv) > 1:
    parameters['batchsize'] = int(sys.argv[1])
    run_id = str(sys.argv[2])
    failure_rate = float(sys.argv[3])
else:
    parameters['batchsize'] = 1
    run_id = 0
    failure_rate = 0

# Invoke lambda function
print("Invoke Lambda function with batchsize: ", parameters['batchsize'])
response = lambda_client.invoke(FunctionName='ComputeGradients', LogType='Tail', Payload=json.dumps(parameters))

# Get job metadata
batch_queue = parameters['batch_queue']
batchsize = parameters['batchsize']

print("Get job meta data")
while True:
    job = batch_client.list_jobs(jobQueue=batch_queue, jobStatus='PENDING')
    if len(job['jobSummaryList']) == 1:
        break
    time.sleep(1)

job_id = job['jobSummaryList'][0]['jobId']
array_size = job['jobSummaryList'][0]['arrayProperties']['size']
print("Array size: ", array_size)

# Create failure schedule or read schedule
if create_schedule is True:
    tmin = 1   # in seconds
    tmax = 390  # in seconds
    schedule = np.random.randint(low=tmin, high=tmax, size=array_size)
else:
    schedule = np.load('shut_down_schedule_100.dat')

failure_rate = np.array([failure_rate])
K = create_failure_schedule(array_size, failure_rate, schedule)
print("Kill schedule: ", K)

# Wait for job to finish
print("Wait for job to finish")
started=False
while True:

    # Check if job has finished
    array_job = batch_client.list_jobs(arrayJobId=job_id, jobStatus='SUCCEEDED')
    if len(array_job['jobSummaryList']) == array_size:
        tend=time.time()
        break

    # Get list of runnning job instances
    if started is False:
        instances = list_instances_cli(ec2_client, state='running')
        if len(instances) >= array_size:
            print("All instances running. Start w/ shutting down of instances.")
            started=True
            running_instances = instances
            tstart=time.time()

    # Shut down random instances if exceeded scheduled runtime
    if started is True:
        tcurr = time.time() - tstart
        for j in range(array_size):
            if K[0, j] <= tcurr and K[0, j] > 0:
                try:
                    ec2_client.terminate_instances(InstanceIds=[running_instances[j]])
                    K[0, j] = 0
                    print("Shut down instance ", running_instances[j], " after ", tcurr, " s.")
                except:
                    print("Couldn't shut down instance.")
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

# Python, Devito and kernel times
T2 = np.zeros(shape=(array_size, 2))
for j in range(array_size):
    key = 'timings_resilience/timings_resilience_' + str(j)
    bucket = parameters['bucket_name']
    while True:
        try:
            tcont = array_get(bucket, key)
            break
        except:
            time.sleep(1)
    T2[j, 0] = tcont[0]
    T2[j, 1] = tcont[1]

TT = np.concatenate((T, T2), axis=1)

# Save results w/ current datetime stamp
timestamp = datetime.datetime.now()
timestamp = str(timestamp).replace(' ','')  # remove spaces
TT.dump('timings_resilience_failure_' + str(int(failure_rate[0]*100)) + '_run_' + str(run_id))

# Delete S3 results
s3_client.delete_object(Bucket=bucket, Key=parameters['variable_path'] + 'chunk_1/' + 'variable_name' + '1')
s3_client.delete_object(Bucket=bucket, Key=parameters['full_gradient_path'] + 'chunk_1/' + 'gradient_name' + '1')
