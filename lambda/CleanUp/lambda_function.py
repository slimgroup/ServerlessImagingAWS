from __future__ import print_function

import boto3
import json

sqs_client = boto3.client('sqs')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):

    num_chunks = event['num_chunks']
    queue_base_name = event['sqs_queue']
    create_queues = event['auto_create_queues']

    if create_queues == 'TRUE':
        try:
            for j in range(num_chunks):

                # Delete event source mappings
                queue_name = queue_base_name + str(j+1)
                queue_url = sqs_client.get_queue_url(QueueName=queue_name)
                arn = 'arn:aws:sqs:' + 'us-east-1' + ':' + queue_url['QueueUrl'][28:-len(queue_name)-1] + \
                    ':' + queue_name
                mappings = lambda_client.list_event_source_mappings(EventSourceArn=arn)
                lambda_client.delete_event_source_mapping(UUID=mappings['EventSourceMappings'][0]['UUID'])

                # Delete queues
                sqs_client.delete_queue(QueueUrl=queue_url['QueueUrl'])

            return event

        except Exception as e:
            print(e)
            message = 'Error deleting SQS queues'
            print(message)
            raise Exception(message)

    else:
        return event
