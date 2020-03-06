from __future__ import print_function
import sys
sys.path.insert(0, '/app/devito-tti')

import numpy as np
import psutil, os, gc, boto3, random, string, time
from PySource import RickerSource, Receiver
from PyModel import Model
from utils import AcquisitionGeometry
from JAcoustic_codegen import forward_modeling, adjoint_born, forward_born, forward_freq_modeling, adjoint_freq_born
from CloudExtras import model_get, array_put, array_get, segy_get, resample, get_chunk_size, restrict_model_to_receiver_grid, extent_gradient
from scipy import ndimage
from devito import Eq, Operator, TimeFunction

tstart = time.time()

# AWS clients
s3_client = boto3.client('s3', region_name='us-east-1')
sqs_client = boto3.client('sqs', region_name='us-east-1')
chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

# Get environment variables
node_idx = int(os.environ["AWS_BATCH_JOB_ARRAY_INDEX"])
iteration = int(os.environ["JUDI_ITERATION"])
num_shots = int(os.environ["NUM_SHOTS"])
batchsize = int(os.environ["BATCHSIZE"])
num_chunks = int(os.environ["NUM_CHUNKS"])
bucket = os.environ["S3_BUCKET"]
queue_names = os.environ["SQS_QUEUE"]

data_path = os.environ["DATA_PATH"]
data_name = os.environ["DATA_NAME"]

model_path = os.environ["MODEL_PATH"]
velocity_name = os.environ["VELOCITY_NAME"]
water_name = os.environ["WATER_NAME"]

variable_path = os.environ["VARIABLE_PATH"]
variable_name = os.environ["VARIABLE_NAME"]
step_length = int(os.environ["STEP_LENGTH"])
step_scaling = int(os.environ["STEP_SCALING"])

partial_gradient_path = os.environ["GRAD_PATH_PARTIAL"]
full_gradient_path = os.environ["GRAD_PATH_FULL"]
gradient_name = os.environ["GRAD_NAME"]

# Fetch models from S3
vp, origin_full, spacing = model_get(bucket, model_path + velocity_name)
water = model_get(bucket, model_path + water_name)[0]
shape_full = vp.shape
ndims = len(spacing)

# 128 shots with maximum number of receivers
shot = np.array(np.arange(1001, 1129))
shot[1] = 1101; shot[2] = 1103; shot[13] = 1104; shot[24] = 1105; shot[35] = 1106;
shot[46] = 1107; shot[57] = 1108; shot[68] = 1109; shot[79] = 1110; shot[90] = 1111;
shot[101] = 1112; shot[112] = 1115; shot[113] = 1116; shot[124] = 1117
shot = np.sort(shot)
idx = shot[node_idx]

#idx = random.randint(1, num_shots)  # fix to certain bsize for constant?
print("Process shot no.: ", idx)
dorig, sx, sz, gx, gz, tn, dt, nt = segy_get(bucket, data_path, data_name + str(idx) + '.segy')

# Restrict models to receiver area + buffer (default is 500 m)
m0, shape, origin = restrict_model_to_receiver_grid(sx, gx, vp, spacing, origin_full, buffer_size=5000)
water = restrict_model_to_receiver_grid(sx, gx, water, spacing, origin_full, buffer_size=5000)[0]

print("Original shape: ", shape_full)
print("New shape: ", shape)

# Load previous iterations
if iteration == 1:
    x = np.zeros(shape=shape, dtype='float32')
else:
    x = array_get(bucket, variable_path + 'chunk_1/' + variable_name + str(iteration-1))
    if num_chunks > 1:
        for chunk in range(1,num_chunks):
            x_chunk = array_get(bucket, variable_path + 'chunk_' + str(chunk+1) + '/' + variable_name + str(iteration-1))
            x = np.concatenate((x, x_chunk), axis=0)
    x = x.reshape(shape[0], shape[1], order='F')
    x = restrict_model_to_receiver_grid(sx, gx, x, spacing, origin_full)[0]

# Set up model structures
model = Model(shape=shape, origin=origin, spacing=spacing, vp=np.sqrt(1/m0))

# Time axis
t0 = 0.
dt_comp = model.critical_dt
nt_comp = int(1 + (tn-t0) / dt_comp) + 1
time_comp = np.linspace(t0, tn, nt_comp)

# Source
f0 = 0.020
src_coordinates = np.empty((1, ndims))
src_coordinates[0, 0] = sx
src_coordinates[0, 1] = sz

# Receiver for predicted data
nrec = len(gx)
rec_coordinates = np.empty((nrec, ndims))
rec_coordinates[:, 0] = gx
rec_coordinates[:, 1] = gz

geometry = AcquisitionGeometry(model, rec_coordinates, src_coordinates, t0=0.0, tn=tn, src_type='Ricker', f0=f0)

# Resample input data to computational grid
dorig = resample(dorig, t0, tn, nt, nt_comp)
dobs = Receiver(name='rec_t', grid=model.grid, ntime=nt_comp, coordinates=rec_coordinates)
dobs.data[:] = dorig

# Predicted data
if iteration > 1:
    dpred = forward_born(model, geometry.src_positions, geometry.src.data, geometry.rec_positions)[0]
    # Residual and function value
    dpred = dpred - dobs
else:
    dpred = Receiver(name='rec', grid=model.grid, ntime=nt_comp, coordinates=rec_coordinates)
    dpred.data[:] = -dorig

# Function value
fval = np.array([.5*np.linalg.norm(dpred.data)**2], dtype='float32')
print("fval, dpred.shape, dobs.shape: ", fval, dpred.shape, dobs.shape)

# Wavefields in memory
t1 = time.time()
checkpointing = True
if checkpointing is False:
    opF, u0 = forward_modeling(model, geometry.src_positions, geometry.src.data, geometry.rec_positions, save=True, u_return=True, op_return=True, tsub_factor=12)
    g = adjoint_born(model, geometry.rec_positions, dpred.data[:], u=u0, is_residual=True, op_forward=opF, tsub_factor=12)[0]
else:
    opF, u0 = forward_modeling(model, geometry.src_positions, geometry.src.data, geometry.rec_positions, save=False, u_return=True, op_return=True)
    g = adjoint_born(model, geometry.rec_positions, dpred.data[:], u=u0, is_residual=True, op_forward=opF, checkpointing=True, maxmem=30000)
t2 = time.time()
print("Save in memory. Time [s]: ", t2 - t1)

# Remove pml and extent back to full size
g = g[model.nbpml:-model.nbpml, model.nbpml:-model.nbpml]  # remove padding
g = extent_gradient(shape_full, origin_full, shape, origin, spacing, g)
g = np.reshape(g, -1, order='F')

# Chunk up gradient and write to bucket. Add gradients to SQS queue
chunk_size = get_chunk_size(len(g), num_chunks)
idx_count = 0
for j in range(num_chunks):

    # Save to bucket
    file_ext = ''.join(random.sample(chars*12, 12))
    key = partial_gradient_path + 'chunk_' + str(j+1) + '/' + gradient_name + file_ext
    gwrite = g[idx_count:idx_count + chunk_size[j]]
    array_put(gwrite, bucket, key)
    idx_count += chunk_size[j]

    # Add to queue
    queue_name = queue_names + str(j+1)
    msg = bucket + '&' + partial_gradient_path + '&' + full_gradient_path + '&' + \
        gradient_name + '&' + file_ext + '&' + str(iteration) + '&1&' + str(batchsize) + \
        '&' + str(j+1) + '&' + queue_name + '&' + variable_path + '&' + variable_name + \
        '&' + str(step_length) + '&' + str(step_scaling)

    # SQS url
    url = 'https://sqs.us-east-1.amazonaws.com/851065145468/' + queue_name

    # Send message
    sqs_client.send_message(QueueUrl=url, DelaySeconds=0, MessageBody=msg)

tfinal = time.time()
print("Time spent running script: ", tfinal - tstart)

# Save timings in bucket
t_devito = t2 - t1
t_script = tfinal - tstart
timings = np.array([t_devito, t_script], dtype='float32')

# Collect timings
filename = 'timings_resilience/timings_resilience_' + str(node_idx)
array_put(timings, bucket, filename)
