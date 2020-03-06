import numpy as np
import boto3, json, time, datetime, sys
import matplotlib.pyplot as plt
from pytz import timezone
from CloudExtras import array_get

# Read parameters
with open('parameters.json', 'r') as filename:
    parameters = json.load(filename)

# EC2 bare metal results
key = 'timings_omp_bare_metal/strong_scaling_omp_bare_metal_numthreads_'
num_cores = np.array([1, 2, 4, 8, 16, 24])
num_files = 9
T = []

for i in range(num_files):
    for run in range(3):
        T = array_get(parameters['bucket_name'], key + str(num_cores[i]) + '_run_' + str(run))
        T.dump('results_bare_metal/timings_strong_scaling_omp_' + str(num_cores[i]) + '_run_' + str(run))
