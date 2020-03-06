# convert timings

from CloudExtras import array_get
import numpy as np
import boto3

bucket = 'slim-bucket-common'
client = boto3.client('s3')

num_instances = np.array([1,2,4,8,16])
num_scalings = len(num_instances)
num_runs_per_scaling = 10

files_r5 = client.list_objects_v2(Bucket=bucket, Prefix='pwitte/timings/r5/mpi_scaling')
num_timings_r5 = len(files_r5['Contents'])
file_list_r5 = []
for j in range(num_timings_r5):
    file_list_r5.append(files_r5['Contents'][j]['Key'])

timings_r5 = []
for batchsize in num_instances:
    run = 0
    for filename in file_list_r5:
        if filename[0:int(41 + len(str(batchsize)))] == 'pwitte/timings/r5/mpi_scaling_num_nodes_' + str(batchsize) + '_':
            t = array_get(bucket, filename)
            t.dump('results/r5/timings_num_nodes_' + str(batchsize) + '_run_' + str(run))
            run += 1


files_c5n = client.list_objects_v2(Bucket=bucket, Prefix='pwitte/timings/c5n/mpi_scaling')
num_timings_c5n = len(files_c5n['Contents'])
file_list_c5n = []
for j in range(num_timings_c5n):
    file_list_c5n.append(files_c5n['Contents'][j]['Key'])

timings_c5n = []
for batchsize in num_instances:
    run = 0
    for filename in file_list_c5n:
        if filename[0:int(42 + len(str(batchsize)))] == 'pwitte/timings/c5n/mpi_scaling_num_nodes_' + str(batchsize) + '_':
            t = array_get(bucket, filename)
            t.dump('results/c5n/timings_num_nodes_' + str(batchsize) + '_run_' + str(run))
            run += 1
