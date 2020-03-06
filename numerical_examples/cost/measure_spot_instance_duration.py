import numpy as np
import boto3, json, time, datetime, sys
import matplotlib.pyplot as plt
from pytz import timezone
from CloudExtras import array_get

# Parameters
instance_type = 'c5n.18xlarge'
ec2_client = boto3.client('ec2')

# Request spot instance
response = ec2_client.request_spot_instances(
    AvailabilityZoneGroup='us-east-1',
    InstanceCount=1,
    LaunchSpecification={
        'SecurityGroupIds': [
            'sg-58967010',
        ],
        'IamInstanceProfile': {
            'Name': 'ec2-spot-profile'
        },
        'ImageId': 'ami-00068cd7555f543d5',
        'InstanceType': instance_type
    },
    Type='one-time',
    InstanceInterruptionBehavior='terminate'
)

# Wait for instance to launch
t1 = time.time()
while True:
    request = ec2_client.describe_spot_instance_requests(
        Filters=[
            {
                'Name': 'state',
                'Values': [
                    'submitted',
                    'active',
                ]
            },
        ],
    )
    try:
        status = request['SpotInstanceRequests'][0]['State']
    except:
        status = 'inactive'

    if status == 'active':
        t2 = time.time()
        break
startup_time_sec = t2 - t1
print('Startup time: ', startup_time_sec)

# Wait until instance is interupted
t3 = time.time()
while True:
    request = ec2_client.describe_spot_instance_requests(
        Filters=[
            {
                'Name': 'state',
                'Values': [
                    'open',
                    'active',
                ]
            },
        ],
    )
    try:
        status = request['SpotInstanceRequests'][0]['State']
    except:
        status = 'inactive'
    
    if status == 'active':
        t4 = time.time()
        break


# Get timings
runtime_sec = t3 - t4
t = np.array([startup_time_sec, runtime_sec])

# Save timings
timestamp = datetime.datetime.now()
timestamp = str(timestamp).replace(' ','')  # remove spaces
t.dump('timings_' + timestamp)

