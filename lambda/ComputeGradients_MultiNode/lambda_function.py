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
        num_nodes = event['num_nodes']
        num_cores = event['omp_num_threads']
        memory = event['memory']
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
        container = event['container']
        batch_queue = event['batch_queue']
        num_retry = event['num_retry']
        thread_pinning = event['thread_pinning']
        instance_type = event['instance_type']
        user_id = event['user_id']
        #min_index = event['min_index']
        #max_index = event['max_index']

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

        # shot_range = np.arange(min_index, max_index+1,step=2)
        #shot_range = np.arange(min_index, max_index+1)
        #shot_indices = np.random.permutation(shot_range)[0:batchsize]

        for i in range(batchsize):

            # Register job definition for current iteration
            job_def = batch_client.register_job_definition(
                jobDefinitionName='isotropic-multi-node-job-' + str(i),
                type='multinode',
                nodeProperties={
                    'numNodes': num_nodes,
                    'mainNode': 0,
                    'nodeRangeProperties': [
                        {
                            'targetNodes': '0:' + str(num_nodes-1),
                            'container': {
                                'image': container,
                                'vcpus': num_cores,
                                'memory': memory,
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
                                        'name': 'NUM_NODES',
                                        'value': str(num_nodes)
                                    },
                                    {
                                        'name': 'NUM_CORES',
                                        'value': str(num_cores)
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
                                        'name': 'USER_ID',
                                        'value': user_id
                                    },
                                ],
                                'volumes': [
                                    {
                                        'host': {
                                            'sourcePath': '/efs'
                                        },
                                        'name': 'efs'
                                    },
                                ],
                                'mountPoints': [
                                    {
                                        'containerPath': '/efs',
                                        'sourceVolume': 'efs'
                                    },
                                ],
                                'instanceType': instance_type
                            }
                        },
                    ]
                },
                retryStrategy={
                    'attempts': num_retry
                }
            )

            # Submit job
            revision = job_def['revision']
            response = batch_client.submit_job(
                jobName='multi-node-batch-' + str(i) + '-iter-' + str(iteration),
                jobQueue=batch_queue,
                jobDefinition='isotropic-multi-node-job-' + str(i) + ':' + str(revision),
            )

            # Save job id
            if i == 0:
                job_ids = response['jobId']
            else:
                job_ids += ('&' + response['jobId'])

        # Write job ids to s3 (too big to save in event)
        timestamp = datetime.datetime.now()
        timestamp = str(timestamp).replace(' ','')  # convert to string and remove spaces
        key = 'logs/multinode_job_ids_' + timestamp
        s3_client.put_object(Body=job_ids.encode(), Bucket=bucket, Key=key)
        event['jobIdFile'] = key

        return event

    except Exception as e:
        traceback.print_exc()
        raise e
