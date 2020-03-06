from __future__ import print_function

import boto3
import json
import time

sqs_client = boto3.client('sqs')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):

    num_chunks = event['num_chunks']
    queue_base_name = event['sqs_queue']
    create_queues = event['auto_create_queues']

    if create_queues == 'TRUE':
        try:
            # One queue per chunk
            arn_list = []
            for j in range(num_chunks):

                # Create queues
                queue_name = queue_base_name + str(j+1)
                attributes = {'DelaySeconds':'0',
                              'ReceiveMessageWaitTimeSeconds': '0',
                              'VisibilityTimeout':'60'}
                queue = sqs_client.create_queue(QueueName=queue_name, Attributes=attributes)

                # Piece together arn from queue meta data (thanks aws)
                arn = 'arn:aws:sqs:' + 'us-east-1' + ':' + queue['QueueUrl'][28:-len(queue_name)-1] + \
                    ':' + queue_name
                lambda_client.create_event_source_mapping(EventSourceArn=arn, FunctionName='ReduceGradients')
                arn_list.append(arn)

            # Wait until all triggers have been activated
            while True:
                count_triggers = 0
                for j in range(num_chunks):
                    status = lambda_client.list_event_source_mappings(EventSourceArn=arn_list[j])
                    if status['EventSourceMappings'][0]['State'] == 'Enabled':
                        count_triggers += 1
                if count_triggers == num_chunks:
                    break
                else:
                    time.sleep(1)

            return event

        except Exception as e:
            print(e)
            message = 'Error setting up SQS queues'
            print(message)
            raise Exception(message)

    else:
        return event
