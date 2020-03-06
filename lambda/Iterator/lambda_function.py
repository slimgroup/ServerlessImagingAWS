import boto3
import traceback

client = boto3.client('s3')

def lambda_handler(event, context):

    iteration = event['iterator']['count']
    maxiter = event['iterator']['maxiter']
    batchsize = event['batchsize']
    bucket = event['bucket_name']
    #nsrc = event['nsrc']

    # Increase index
    iteration = iteration + 1
    event['iterator']['count'] = iteration
    if iteration <= maxiter:
        event['iterator']['continue'] = True
    else:
        event['iterator']['continue'] = False

    return event
