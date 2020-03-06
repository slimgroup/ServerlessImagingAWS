from __future__ import print_function
import boto3
import traceback
import datetime
import numpy as np

batch_client = boto3.client('batch')
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

def gradient_handler(event, context):

    try:
        iteration = event['iterator']['count']
        batchsize = event['batchsize']
        num_shots = event['num_shots']
        bucket = event['bucket_name']
        partial_gradient_path = event['partial_gradient_path']
        full_gradient_path = event['full_gradient_path']
        gradient_name = event['gradient_name']
        model_path = event['model_path']
        velocity_name = event['velocity_name']
        water_name = event['water_name']
        variable_path = event['variable_path']
        variable_name = event['variable_name']
        script_path = event['script_path']
        script_name = event['script_name']
        data_path = event['data_path']
        data_name = event['data_name']
        sqs_queue = event['sqs_queue']
        num_chunks = event['num_chunks']
        step_length = event['step_length']
        step_scaling = event['step_scaling']
        num_retry = event['num_retry']
        omp_num_threads = event['omp_num_threads']
        multi_socket = event['multi_socket']
        memory = event['memory']
        container = event['container']
        batch_queue = event['batch_queue']
        thread_pinning = event['thread_pinning']
        omp_places = event['omp_places']
        instance_type = event['instance_type']
        space_order = event['space_order']

        # Purge queues for new iteration
        queue_list = sqs_client.list_queues()
        print(queue_list['QueueUrls'])
        for j in range(1, num_chunks+1):
            queue_name = sqs_queue + str(j)
            print(queue_name)
            for url in queue_list['QueueUrls']:
                if url[-len(queue_name):] == queue_name:
                    queue_url = url
            try:
                sqs_client.purge_queue(QueueUrl=queue_url)
            except:
                raise Exception('Error purging queue')

        # Determine number of cores per instance
        if multi_socket == 'TRUE':
                num_cores = 2*omp_num_threads
        else:
                num_cores = omp_num_threads

        # Register job definition for current iteration
        job_def = batch_client.register_job_definition(
            jobDefinitionName='isotropic-single-instance-batch',
            type='container',
            containerProperties={
                'image': container,
                'vcpus': num_cores,
                'memory': memory,
                #'instanceType': instance_type,
                'environment': [
                    {
                        'name': 'JUDI_ITERATION',
                        'value': str(iteration)
                    },
                    {
                        'name': 'NUM_SHOTS',
                        'value': str(num_shots)
                    },
                    {
                        'name': 'BATCHSIZE',
                        'value': str(batchsize)
                    },
                    {
                        'name': 'NUM_CHUNKS',
                        'value': str(num_chunks)
                    },
                    {
                        'name': 'OMP_NUM_THREADS',
                        'value': str(omp_num_threads)
                    },
                    {
                        'name': 'S3_BUCKET',
                        'value': bucket
                    },
                    {
                        'name': 'GRAD_PATH_PARTIAL',
                        'value': partial_gradient_path
                    },
                    {
                        'name': 'GRAD_PATH_FULL',
                        'value': full_gradient_path
                    },
                    {
                        'name': 'GRAD_NAME',
                        'value': gradient_name
                    },
                    {
                        'name': 'MODEL_PATH',
                        'value': model_path
                    },
                    {
                        'name': 'VELOCITY_NAME',
                        'value': velocity_name
                    },
                    {
                        'name': 'WATER_NAME',
                        'value': water_name
                    },
                    {
                        'name': 'VARIABLE_PATH',
                        'value': variable_path
                    },
                    {
                        'name': 'VARIABLE_NAME',
                        'value': variable_name
                    },
                    {
                        'name': 'SCRIPT_PATH',
                        'value': script_path
                    },
                    {
                        'name': 'SCRIPT_NAME',
                        'value': script_name
                    },
                    {
                        'name': 'DATA_PATH',
                        'value': data_path
                    },
                    {
                        'name': 'DATA_NAME',
                        'value': data_name
                    },
                    {
                        'name': 'SQS_QUEUE',
                        'value': sqs_queue
                    },
                    {
                        'name': 'STEP_LENGTH',
                        'value': str(step_length)
                    },
                    {
                        'name': 'STEP_SCALING',
                        'value': str(step_scaling)
                    },
                    {
                        'name': 'THREAD_PINNING',
                        'value': thread_pinning
                    },
                    {
                        'name': 'MULTI_SOCKET',
                        'value': multi_socket
                    },
                    {
                        'name': 'OMP_PLACES',
                        'value': omp_places
                    },
                    {
                        'name': 'SPACE_ORDER',
                        'value': str(space_order)
                    },
                ],
            },
            retryStrategy={
                    'attempts': num_retry
            }
        )

        # Submit job
        revision = job_def['revision']
        if batchsize > 1:
            response = batch_client.submit_job(
                jobName='isotropic-single-instance-jobs-' + str(iteration),
                jobQueue=batch_queue,
                arrayProperties={
                        'size': batchsize
                },
                jobDefinition='isotropic-single-instance-batch:' + str(revision),
            )
        else:
            response = batch_client.submit_job(
                jobName='isotropic-single-instance-jobs-' + str(iteration),
                jobQueue=batch_queue,
                jobDefinition='isotropic-single-instance-batch:' + str(revision),
            )

        print('Registered job for iteration {} with batchsize {}'.format(iteration, batchsize))
        event['jobId'] = response['jobId']

        return event

    except Exception as e:
        traceback.print_exc()
        raise e
