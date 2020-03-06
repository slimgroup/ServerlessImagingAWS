from __future__ import print_function
import sys
sys.path.insert(0, '/app/devito_isotropic')
import boto3, subprocess, os

sqs_client = boto3.client('sqs', region_name='us-east-1')

queue_names = os.environ["SQS_QUEUE"]
num_chunks = int(os.environ["NUM_CHUNKS"])
user_id = os.environ["USER_ID"]

for j in range(num_chunks):

    # Add to queue
    queue_name = queue_names + str(j+1)

    # Read message
    text_file = open("/efs/scratch/devito/sqs_command_" + str(j), "r")
    msg = text_file.read()
    text_file.close()
    print("Message: ", msg)

    # Piece together url name for SQS endpoint
    #url = 'https://sqs.us-east-1.amazonaws.com/851065145468/' + queue_name
    url = 'https://sqs.us-east-1.amazonaws.com/' + user_id + '/' + queue_name

    subprocess.run(["aws", "sqs", "send-message", "--region", "us-east-1", "--endpoint-url", "https://sqs.us-east-1.amazonaws.com", "--queue-url", url, "--message-body", msg])
