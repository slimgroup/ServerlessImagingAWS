
from __future__ import print_function

import boto3
import time
import json

s3_client = boto3.client('s3')
batch_client = boto3.client('batch')
sqs_client = boto3.client('sqs')

def lambda_handler(event, context):

    # Get event parameters
    iteration = event['iterator']['count']
    bucket = event['bucket_name']
    num_chunks = event['num_chunks']
    variable_path = event['variable_path']
    variable_name = event['variable_name']
    partial_grad_path = event['partial_gradient_path']
    full_grad_path = event['full_gradient_path']
    grad_name = event['gradient_name']
    batchsize = event['batchsize']
    queue_name = event['sqs_queue']
    step_length = event['step_length']
    step_scaling = event['step_scaling']
    job_file = event['jobIdFile']

    try:
        # Load Ids of batch jobs
        objects = s3_client.get_object(Bucket=bucket, Key=job_file)
        job_ids = objects['Body'].read().decode()
        job_list = job_ids.split('&')
        num_jobs = len(job_list)

        # Check run time of current jobs
        runtime = []
        for j in range(num_jobs):
            response = batch_client.describe_jobs(jobs=[job_list[j]])
            job_status = response['jobs'][0]['status']
            if job_status == 'RUNNING' or job_status == 'SUCCEEDED':
                job_start_time = response['jobs'][0]['startedAt']
            if job_status == 'SUCCEEDED':
                job_end_time = response['jobs'][0]['stoppedAt']
                runtime.append(job_end_time - job_start_time)

        # Compute average run time of finished jobs
        num_succeeded = len(runtime)
        fraction_finished = num_succeeded / batchsize
        print("Jobs finished (percent): ", fraction_finished * 100)
        if fraction_finished > 0:
            average_runtime = 0
            for j in range(num_succeeded):
                average_runtime += runtime[j]
            average_runtime /= num_succeeded
            print("Average runtime [minutes]: ", average_runtime/1e3/60)

        # If specified percentage of jobs have finished -> kill any job that exceeds 1.5*average run time
        count_jobs = 0
        cancelled_jobs = 0
        for j in range(num_jobs):
            response = batch_client.describe_jobs(jobs=[job_list[j]])
            job_status = response['jobs'][0]['status']
            if job_status == 'RUNNING':
                job_start_time = response['jobs'][0]['startedAt']
                current_time = int(time.time()*1e3)
                runtime = current_time - job_start_time
                #if fraction_finished >= .5:
                if num_succeeded > 1:   # wait until at least two other jobs have finished
                    if runtime > 1.5 * average_runtime:
                        # cancel job
                        batch_client.terminate_job(jobId=job_list[j], reason='Exceeded time limit.')
                        #print("Terminated job ", job_list[j])
            elif job_status == 'SUCCEEDED' or job_status == 'FAILED':
                count_jobs += 1
            if job_status == 'FAILED':
                cancelled_jobs += 1

        # If all jobs have finished with at least 1 failed job, send signal to proceed to image/model update
        if count_jobs == num_jobs and cancelled_jobs > 0:

            # Send message to every queue
            for j in range(1, num_chunks+1):
                current_queue = queue_name + str(j)

                # Loop over queues
                queue_list = sqs_client.list_queues()
                for url in queue_list['QueueUrls']:
                    if url[-len(current_queue):] == current_queue:
                        queue_url = url

                msg = bucket + '&' + partial_grad_path + '&' + full_grad_path + '&' + grad_name + '&' + 'PROCEED' + '&' \
                    + str(iteration) + '&' + str(-1) + '&' + str(batchsize) + '&' + str(j) + '&' \
                    + current_queue + '&' + variable_path + '&' + variable_name + '&' + str(step_length) \
                    + '&' + str(step_scaling)

                try:
                    sqs_client.send_message(QueueUrl=queue_url, MessageBody=msg, DelaySeconds=0)
                except:
                    raise Exception('Specified queue name does not exist.')

        # Check if all updated image/model chunks are available -> proceed to next iteration
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
