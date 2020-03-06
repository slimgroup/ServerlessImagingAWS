import os, json
import numpy as np
from CloudExtras import model_get, array_put, array_get, image_mute, image_scaling, data_mute
import matplotlib.pyplot as plt
from PyModel import Model
from scipy import ndimage

# Get parameters from json file
with open('parameters.json', 'r') as filename:
    parameters = json.load(filename)

# Get result
filename = 'lsrtm_sgd_30.dat'
if os.path.isfile(filename):
    x = np.load(filename)
else:
    # Load image
    x = array_get(parameters['bucket_name'], parameters['variable_path'] + 'chunk_1/' + parameters['variable_name'] + str(30))
    x = np.reshape(x[1:], (10789, 1911), order='F')
    x.dump(filename)

spacing = 6.26
shape = x.shape
xmax = (shape[0]-1)*spacing/1e3
zmax = (shape[1]-1)*spacing/1e3

# Linear depth scaling
filter = np.linspace(start=0, stop=1, num=x.shape[1])
for j in range(x.shape[0]):
    x[j, :] = x[j, :] * filter

# High pass filter to remove low frequency artifacts
xlow = ndimage.gaussian_filter(x, 8)
xhigh = x - xlow

# Plot
fig, ax = plt.subplots(figsize=(6.66, 2))
plt.imshow(np.transpose(xhigh), aspect='auto', cmap='seismic', vmin=-4.5e-1, vmax=4.5e-1, extent=[0, xmax, zmax, 0])
ax.set_xlabel('Lateral position [km]', fontsize=10)
ax.set_ylabel('Depth [km]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
plt.xticks(np.array([0,10,20,30,40,50,60]), ('0','10', '20', '30', '40', '50', '60'))
plt.yticks(np.array([0,2,4,6,8,10]), ('0','2', '4', '6', '8', '10'))
cb = plt.colorbar()
cb.set_label(r'Slowness$^2$ $[s^2/km^2]$', rotation=90, fontsize=9)
cb.ax.set_yticklabels(['-0.2', '0', '0.2'])  # vertically oriented colorbar
cb.ax.tick_params(labelsize=9)

ax.yaxis.set_ticks_position('left')
plt.tight_layout()
plt.savefig('lsrtm_sgd.png', dpi=300, format='png')
os.system('mogrify -trim lsrtm_sgd.png')



########################################################################################################################

# Cost
num_iter = 30
batchsize = 80
num_shots = 1348
job_duration = 600*60   # seconds (30 iteration a 20 minutes)
job_duration_in_hours = job_duration / 60 / 60
cost_lambda = 0
cost_s3 = 0
cost_sqs = 0

# Step function cost
num_steps = 2 + 6*num_iter + 3 + 20*30*2
step_price = 0.025  # $ per 1,000 transitions
cost_step = num_steps * step_price/1000

# Cost EC2
container_runtime = 250/60/60   # hours
ec2_cost_spot = 0.3155
ec2_cost_on_demand = 0.80
ec2_cost_reserved_1 = 0.301 # 3 year all upfront
ec2_cost_reserved_2 = 0.463 # 1 year all upfront

cost_ec2_spot = container_runtime * ec2_cost_spot * batchsize * num_iter
cost_ec2_on_demand = container_runtime * ec2_cost_on_demand * batchsize * num_iter
cost_ec2_on_reserved_1 = container_runtime * ec2_cost_reserved_1 * batchsize * num_iter
cost_ec2_on_reserved_2 = container_runtime * ec2_cost_reserved_2 * batchsize * num_iter

# Cost Lambda (s)
lambda_runtime_per_iteration = (4840 * 98.6 + 4060 * 96.4 + 935 * 54.2 + 5120 * 64 + 6800 * 71 + 5090 * 84.5 + 3200 * 55 + 7960 * 70 + 6990 * 65 + 3060 * 70.2 + 4710 * 61.6 + 6290 * 63.7 + 7850 * 72.7 + 1760 * 54.8 + 4460 * 56.2 + 9820 * 70.3 + 6190 * 66 + 1940 * 54.1 + 5260 * 51.2 + 8100 * 63.3 + 9430 * 66.4 + 623 * 73.2 + 3430 * 61.7 + 8610 * 71.4 + 7080 * 69.5 + 1610 * 59 + 5050 * 54.1 + 6340 * 78.8 + 3130 * 57.5)/ 1000 / 8
cost_lambda_1280 = 0.000016667 / 1024 * 1280

lambda_invokations = (4840 + 4060 + 935 + 5120 + 6800 + 5090 + 3200 + 7960 + 6990 + 3060 + 4710 + 6290 + 7850 + 1760 + 4460 + 9820 + 6190 + 1940 + 5260 + 8100 + 9430 + 623 + 3430 + 8610 + 7080 + 1610 + 5050 + 6340 + 3130)/8*30

cost_lambda = lambda_runtime_per_iteration * cost_lambda_1280 * num_iter + lambda_invokations * 0.2/1000000

# Cost S3

# I: Storage
s3_storage_size = 100*0.080 + 11.9  # size of data, models + gradients in GB
cost_s3_storage = job_duration_in_hours * s3_storage_size * 0.023 / 30 / 24 # S3 price per GB-hour

# II: Requests and retrievals
grad_num_read = (80 + 40 + 20 + 10 + 5 + 4 + 2 + 1) * num_iter
grad_num_write = num_iter * batchsize +  (40 + 20 + 10 + 5 + 4 + 2 + 1) * num_iter
model_read = num_iter * 2
cost_s3_req_ret = (grad_num_read + model_read) * 0.0004/1000 + grad_num_write * 0.005/1000

# III: Data transfer
# No data transfer between S3 and EC2 instance in the same region
cost_s3_transfer = 0

# IV: Management
s3_cost_listing = 0.0025/1000000 * num_iter * 20
cost_s3 = cost_s3_storage + cost_s3_req_ret + cost_s3_transfer + s3_cost_listing

# Cost SQS
cost_sqs_request = 0.0000004
cost_sqs = (lambda_invokations + num_iter*batchsize)*cost_sqs_request

# Plot
fig, ax = plt.subplots(figsize=(3.15, 3))
ax.bar(np.array([2,3,4,5]), np.array([cost_lambda, cost_sqs, cost_step, cost_s3]), align='center', alpha=0.8, ecolor='black', width=0.5, capsize=3)
ax.bar(1, cost_ec2_spot, align='edge', alpha=0.8, ecolor='black', width=.3, capsize=3)
ax.bar(1, cost_ec2_on_demand, align='edge', alpha=0.8, ecolor='black', width=-.3, capsize=3, color='#1f77b4')
ax.set_yscale('log')
ax.set_xlim([0.25, 5.75])
ax.set_ylim([0, 500])
plt.legend(['on-demand', 'spot'], loc='upper right', fontsize=10)

ax.text(.45, 180, str(133), color='#1f77b4', fontsize=10, fontweight='bold')
ax.text(1.05, 70, str(52), color='#F39C12', fontsize=10, fontweight='bold')
y2 = [0.91, 0.23, 0.03, 0.03]
xloc = [1.55, 2.55, 3.45, 4.65]
yloc = [1.25, 0.3, 0.045, 0.045]
for j in range(len(y2)):
    ax.text(xloc[j], yloc[j], str(y2[j]), color='#1f77b4', fontsize=10, fontweight='bold')

plt.xticks(np.array([1,2,3,4,5]), ('EC2', '$\lambda$', 'SQS', 'Step', 'S3'), fontsize=10)
plt.yticks(np.array([.1,1,10,100]), ('0.1', '1', '10', '100'), fontsize=10)

#ax.set_xlabel('Service', fontsize=10)
ax.set_ylabel('Cost [$]', fontsize=10)
ax.set_xlabel('. ', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)

plt.tight_layout()
plt.savefig('lsrtm_cost.png', dpi=300, format='png')
os.system('mogrify -trim lsrtm_cost.png')

plt.show()
