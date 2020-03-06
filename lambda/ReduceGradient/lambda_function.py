# Function from deployment package

from __future__ import print_function
import json, boto3, random, string
import numpy as np
import time

client = boto3.client('s3')
queue = boto3.client('sqs')
chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

####################################################################################################
# Auxiliary functions

def get_queue_url(client, queue_name):

    # Get url of sqs queue
    queue_list = client.list_queues()
    for url in queue_list['QueueUrls']:
        if url[-len(queue_name):] == queue_name:
            queue_url = url
    try:
        return queue_url
    except:
        raise Exception('Specified queue name does not exist')


def extract_message(record):
    msg = record['body']
    return msg  #[start:end]


def extract_parameters(msg):
    msg_list = msg.split('&')

    # Extract parameters
    bucket = msg_list[0]
    partial_path = msg_list[1]
    full_path = msg_list[2]
    grad_name = msg_list[3]
    idx = msg_list[4]
    iteration = msg_list[5]
    count = int(msg_list[6])
    batchsize = int(msg_list[7])
    chunk = msg_list[8]
    queue_name = msg_list[9]
    variable_path = msg_list[10]
    variable_name = msg_list[11]
    step_length = int(msg_list[12])
    step_scaling = int(msg_list[13])

    return bucket, partial_path, full_path, grad_name, idx, iteration, count, batchsize, \
        chunk, queue_name, variable_path, variable_name, step_length, step_scaling

def get_array(client, bucket, filename, byte_start=None, byte_end=None):

    # Get data type
    tags = client.get_object_tagging(Bucket=bucket, Key=filename)
    try:
        for tag in tags['TagSet']:
                if tag['Key'] == 'eltype':
                    dtype=tag['Value']

        # Read in gradient and convert to numpy array
        if byte_start is not None and byte_end is not None:
            byte_range = 'bytes=' + str(byte_start) + '-' + str(byte_end)
            b = client.get_object(Bucket=bucket, Key=filename, Range=byte_range)
        else:
            b = client.get_object(Bucket=bucket, Key=filename)

        s = b['Body'].read()
        x = np.fromstring(s, dtype=dtype)
        return x
    except:
        raise Exception('could not retrieve array')

def get_queue_url(client, queue_name):

    # Get url of sqs queue
    queue_list = client.list_queues()
    for url in queue_list['QueueUrls']:
        if url[-len(queue_name):] == queue_name:
            queue_url = url
    try:
        return queue_url
    except:
        raise Exception('Specified queue name does not exist')


def check_for_file(client, bucket, partial_path, chunk, grad_name, idx):
    file_key = partial_path + 'chunk_' + chunk + '/' + grad_name + idx
    files = client.list_objects(Bucket=bucket, Prefix=partial_path + 'chunk_' + chunk + '/' + grad_name)
    check = False
    if 'Contents' in files:
        for filename in files['Contents']:
            if filename['Key'] == file_key:
                check = True
    return check


def get_multipart_file_params(client, bucket, partial_path, grad_name, idx, chunk):

    key = partial_path + 'chunk_' + chunk + '/' + grad_name + idx
    meta = client.head_object(Bucket=bucket, Key=key)   # get size of first gradient in event
    num_bytes = meta['ContentLength']
    min_bytes = 5*1024**2   # minimum number of bytes for first object in multi-part object
    desired_part_size = 500 * 1024**2    # want part size of 500 MB

    # Determine number or parts and size of final part
    if num_bytes <= min_bytes or num_bytes <= desired_part_size:
        num_parts = 1
        residual_bytes = num_bytes
    else:
        num_parts = int(num_bytes/desired_part_size)
        if num_bytes % desired_part_size > 0:
            num_parts += 1
            residual_bytes = num_bytes % desired_part_size
        else:
            residual_bytes = None
    return num_parts, desired_part_size, residual_bytes, num_bytes


def remove_original_gradients(client, event):

    num_gradients = len(event['Records'])
    for j in range(num_gradients):
        msg = extract_message(event['Records'][j])
        bucket, partial_path, full_path, grad_name, idx, iteration, count, batchsize, chunk \
            = extract_parameters(msg)[0:9]

        print("Delete old file: " + partial_path + 'chunk_' + chunk + '/' + grad_name + idx)
        client.delete_object(Bucket=bucket, Key=partial_path + 'chunk_' + chunk + '/' + grad_name + idx)
    return {'statusCode':200}

def get_status(event):

    num_events = len(event['Records'])
    proceed = False
    for msg in event['Records']:
        msg_list = msg['body'].split('&')
        if msg_list[4] == 'PROCEED':
            proceed = True

    if num_events > 1 and proceed is False:
        status = 'REDUCE'
    elif num_events > 1 and proceed is True:
        status = 'RETURN'
    elif num_events == 1:
        status = 'UPDATE'

    return status


def update_count(s3_client, event):

    # Loop over events, check if files still exist and update counter
    new_count = 0
    for records in event['Records']:
        msg = extract_message(records)
        bucket, partial_path, full_path, grad_name, idx, iteration, count, batchsize, chunk \
            = extract_parameters(msg)[0:9]
        if check_for_file(s3_client, bucket, partial_path, chunk, grad_name, idx):
            new_count += count
    return new_count


####################################################################################################

def lambda_handler(event, context):

    status = get_status(event)

    # Only one message in event
    if status == 'UPDATE':  #len(event['Records']) == 1:

        msg = extract_message(event['Records'][0])
        bucket, partial_path, full_path, grad_name, idx, iteration, count, batchsize, \
            chunk, queue_name, variable_path, variable_name, step_length, step_scaling \
            = extract_parameters(msg)

        if count < 0:   # message comes from lambda function -> interupt gradient computation and continue w/ current gradients
            key = partial_path + 'chunk_' + chunk + '/' + grad_name

            # If more than one gradient is left, wait until remaining files have been summed into single file
            while True:
                grad_list = client.list_objects(Bucket=bucket, Prefix=key)
                num_files = len(grad_list['Contents'])
                if num_files == 1:
                    break
                else:
                    time.sleep(1)

            full_key = grad_list['Contents'][0]['Key']
            idx_len = len(full_key) - len(key)
            idx = full_key[-idx_len:]
            count = batchsize

        # Final gradient: update image w/ SGD and save the image and gradient
        if count == batchsize:

            # Check array if it still exists
            if check_for_file(client, bucket, partial_path, chunk, grad_name, idx):

                # Initialize multi-part objects
                num_parts, desired_part_size, residual_bytes, file_size = get_multipart_file_params(client, bucket, partial_path, grad_name, idx, chunk)

                new_key_gradient = full_path + 'chunk_' + chunk + '/' +  grad_name + 'iteration_' + iteration
                multi_part_gradient = client.create_multipart_upload(Bucket=bucket, Key=new_key_gradient)
                parts_list_gradient = []

                new_key_variable = variable_path + 'chunk_' + chunk + '/' + variable_name + iteration
                multi_part_variable = client.create_multipart_upload(Bucket=bucket, Key=new_key_variable)
                parts_list_variable = []

                byte_count = 0
                #step_length = 0
                for part in range(num_parts):

                    # Get byte range
                    byte_start = byte_count  # byte start
                    if residual_bytes is not None and part == (num_parts-1):
                        byte_end = byte_count + residual_bytes - 1
                    else:
                        byte_end = byte_count + desired_part_size - 1   # byte end

                    # Get gradient of current byte range
                    g = get_array(client, bucket, partial_path + 'chunk_' + chunk + '/' + grad_name + idx, byte_start, byte_end)

                    # Write final gradient part
                    print("Write final gradient to bucket: " + new_key_gradient + ' part ' + str(part))
                    multi_part_upload_gradient = client.upload_part(Bucket=bucket, Body=g.tostring(), Key=multi_part_gradient['Key'], \
                        PartNumber=part+1, UploadId=multi_part_gradient['UploadId'])
                    parts_list_gradient.append({'ETag': multi_part_upload_gradient['ETag'] , 'PartNumber': part+1})

                    # Step size
                    if step_scaling < 0:
                       step_length = step_length / np.abs(step_scaling)
                    else:
                       step_length = step_length * np.abs(step_scaling)
                    #step_length = 2*g[0]/np.linalg.norm(g[1:].reshape(-1))**2

                    # Update image w/ final gradient
                    if int(iteration) > 1:
                        x = get_array(client, bucket, variable_path + 'chunk_' + chunk + '/' + \
                            variable_name + str(int(iteration)-1), byte_start, byte_end)

                        # Steepest descent update rule
                        x -= step_length * g
                    else:
                        x = -step_length * g

                    # Write updated image
                    print("Write updated image to bucket: " + new_key_variable + ' part ' + str(part))
                    multi_part_upload_variable = client.upload_part(Bucket=bucket, Body=x.tostring(), Key=multi_part_variable['Key'], \
                        PartNumber=part+1, UploadId=multi_part_variable['UploadId'])
                    parts_list_variable.append({'ETag': multi_part_upload_variable['ETag'] , 'PartNumber': part+1})
                    byte_count += desired_part_size

                # Finalize files
                try:
                    client.complete_multipart_upload(Bucket=bucket, Key=new_key_gradient, UploadId=multi_part_gradient['UploadId'], MultipartUpload={'Parts': parts_list_gradient})
                    client.put_object_tagging(Bucket=bucket, Key=new_key_gradient, Tagging={'TagSet':[{'Key':'eltype','Value':'float32'}, {'Key':'creator','Value':'S3-SLIM'},]})

                    client.complete_multipart_upload(Bucket=bucket, Key=new_key_variable, UploadId=multi_part_variable['UploadId'], MultipartUpload={'Parts': parts_list_variable})
                    client.put_object_tagging(Bucket=bucket, Key=new_key_variable, Tagging={'TagSet':[{'Key':'eltype','Value':'float32'}, {'Key':'creator','Value':'S3-SLIM'},]})

                    # Check that files have been uploaded
                    while True:
                        head1 = client.head_object(Bucket=bucket, Key=new_key_gradient)
                        head2 = client.head_object(Bucket=bucket, Key=new_key_variable)
                        if head1['ContentLength'] == file_size and head2['ContentLength'] == file_size:
                            break
                        else:
                            time.sleep(1)

                    # Remove old gradient file
                    client.delete_object(Bucket=bucket, Key=partial_path + 'chunk_' + chunk + '/' + grad_name + idx)

                    return {
                        'statusCode': 200,
                        'body': json.dumps('Successfully processed gradients.')
                    }
                except:
                    client.abort_multipart_upload(Bucket=bucket, Key=new_key_gradient, UploadId=multi_part_gradient['UploadId'])
                    client.abort_multipart_upload(Bucket=bucket, Key=new_key_variable, UploadId=multi_part_variable['UploadId'])
                    return {
                        'statusCode': 204,
                        'body': json.dump('Error during gradient reduction.')
                    }

        else:
            # Return message to queue
            if check_for_file(client, bucket, partial_path, chunk, grad_name, idx):
                print("Return message to queue")
                url = get_queue_url(queue, queue_name)
                queue.send_message(QueueUrl=url, MessageBody=msg, DelaySeconds=0)

    # More than one message -> sum gradients
    elif status == 'REDUCE':

        # Initialize multi-part object
        msg = extract_message(event['Records'][0])
        bucket, partial_path, full_path, grad_name, idx, iteration, count, batchsize, chunk = extract_parameters(msg)[0:9]
        num_parts, desired_part_size, residual_bytes, file_size = get_multipart_file_params(client, bucket, partial_path, grad_name, idx, chunk)
        file_ext = ''.join(random.sample(chars*12, 12))   # random extension for new file
        new_key = partial_path + 'chunk_' + chunk + '/' + grad_name + file_ext    # new gradient file
        multi_part_object = client.create_multipart_upload(Bucket=bucket, Key=new_key)
        parts_list = []

        # Loop over parts
        byte_count = 0
        #part_count = 0
        for part in range(num_parts):

            # Loop over records (i.e. gradients)
            record_count = 0
            for record in event['Records']:

                # Get current gradient
                msg = extract_message(record)
                bucket, partial_path, full_path, grad_name, idx, iteration, count, batchsize, chunk, queue_name, \
                    variable_path, variable_name, step_length, step_scaling = \
                    extract_parameters(msg)
                print('Process message ' + str(count) + ' of ' + str(len(event['Records'])))

                # Check if file still exists, because SQS sometimes sends messages multiple times
                if check_for_file(client, bucket, partial_path, chunk, grad_name, idx):

                    # Get byte range
                    byte_start = byte_count  # byte start
                    if residual_bytes is not None and part == (num_parts-1):
                        byte_end = byte_count + residual_bytes - 1
                    else:
                        byte_end = byte_count + desired_part_size - 1   # byte end

                    # Get current byte stream
                    g = get_array(client, bucket, partial_path + 'chunk_' + chunk + '/' + grad_name + idx, byte_start, byte_end)

                    if record_count == 0:
                        grad_sum = g
                        #if part_count == 0:
                        #    count_new = count
                    else:
                        grad_sum += g
                        #if part_count == 0:
                        #    count_new += count
                    record_count += 1

            # Upload reduced part to multipart file
            multi_part_upload = client.upload_part(Bucket=bucket, Body=grad_sum.tostring(), Key=multi_part_object['Key'], \
                PartNumber=part+1, UploadId=multi_part_object['UploadId'])
            parts_list.append({'ETag': multi_part_upload['ETag'] , 'PartNumber': part+1})
            byte_count += desired_part_size
            #part_count += 1

        try:
            # Finalize file
            print('Finalize new file: ', new_key)
            client.complete_multipart_upload(Bucket=bucket, Key=new_key, UploadId=multi_part_object['UploadId'], MultipartUpload={'Parts': parts_list})
            client.put_object_tagging(Bucket=bucket, Key=new_key, Tagging={'TagSet':[{'Key':'eltype','Value':'float32'}, {'Key':'creator','Value':'S3-SLIM'},]})

            # Check that file has been uploaded
            while True:
                head = client.head_object(Bucket=bucket, Key=new_key)
                if head['ContentLength'] == file_size:
                    break
                else:
                    time.sleep(1)

            # Update count
            count_new = update_count(client, event)

            # Remove original files
            status = remove_original_gradients(client, event)

            # Add new file to queue
            msg = bucket + '&' + partial_path + '&' + full_path + '&' + grad_name + '&' + file_ext + '&' + iteration + '&' + str(count_new) + '&' + str(batchsize) + '&' + chunk + '&' \
            + queue_name + '&' + variable_path + '&' + variable_name + '&' + str(step_length) \
            + '&' + str(step_scaling)
            url = get_queue_url(queue, queue_name)
            queue.send_message(QueueUrl=url, MessageBody=msg, DelaySeconds=0)

            return {
                'statusCode': 200,
                'body': json.dumps('Successfully processed gradients.')
            }
        except:
            client.abort_multipart_upload(Bucket=bucket, Key=new_key, UploadId=multi_part_object['UploadId'])
            return {
                'statusCode': 204,
                'body': json.dump('Error during gradient reduction.')
            }
    elif status == 'RETURN':

        # Return all messages to queue
        for record in event['Records']:
            msg = extract_message(record)
            queue_name = extract_parameters(msg)[9]

            # Return message to queue
            url = get_queue_url(queue, queue_name)
            queue.send_message(QueueUrl=url, MessageBody=msg, DelaySeconds=0)

    else:
        raise Exception('Specified status not known.')
