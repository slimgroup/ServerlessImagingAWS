from __future__ import print_function

import boto3
import time
import json

s3_client = boto3.client('s3')
batch_client = boto3.client('batch')

def lambda_handler(event, context):

    # Log the received event
    print("Received event: " + json.dumps(event, indent=2))

    # Get current iteration number
    iteration = event['iterator']['count']
    num_chunks = event['num_chunks']
    variable_path = event['variable_path']
    variable_name = event['variable_name']
    job_id = event['jobId']

    try:

        # Check if job stil runs
        response = batch_client.describe_jobs(
            jobs=[job_id]
        )
        job_status = response['jobs'][0]['status']
        if job_status == 'FAILED':
            raise Exception("Batch job failed")

        # Check if all variable chunks are available
        var_count = 0
        for j in range(1, num_chunks+1):

            # Check if sub-folder exists
            filename = variable_path + 'chunk_' + str(j) + '/' + variable_name
            files = s3_client.list_objects(Bucket=event['bucket_name'], Prefix=filename)

            if 'Contents' in files:
                if len(files['Contents']) == iteration:
                    var_count += 1    # 'SUCCEEDED'
                else:
                    var_count += 0    # 'PENDING'
            else:
                var_count += 0    # 'PENDING'

        if var_count == num_chunks:
            var_status = 'SUCCEEDED'
        else:
            var_status = 'PENDING'

        return var_status

    except Exception as e:
        print(e)
        message = 'Error getting Variable status'
        print(message)
        raise Exception(message)
