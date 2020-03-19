import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick
from matplotlib.ticker import NullFormatter

# Load timings
cwd = os.getcwd()
path_default = cwd + '/results/results_batch/'
path_no_ht = cwd + '/results/results_batch_no_ht/'
path_ec2 = cwd + '/results/results_bare_metal/'
path_optimum = cwd + '/results/results_optimum/'

file_list_default = os.listdir(path_default)
file_list_no_ht = os.listdir(path_no_ht)
file_list_ec2 = os.listdir(path_ec2)
file_list_optimum = os.listdir(path_optimum)

file_timings_default = []
file_timings_no_ht = []
file_timings_ec2 = []
file_timings_optimum = []

num_cores_default = np.array([1, 2, 4, 8, 16, 24, 32, 40, 48, 64, 96])
num_cores_no_ht = np.array([1, 2, 4, 8, 16, 24, 32, 40, 48])
num_cores_ec2 = np.array([1, 2, 4, 8, 16, 24, 32, 40, 48])
num_cores_optimum = np.array([1, 2, 4, 8, 10, 12, 16, 20])

num_scalings_default = len(num_cores_default)
num_scalings_no_ht = len(num_cores_no_ht)
num_scalings_ec2 = len(num_cores_ec2)
num_scalings_optimum = len(num_cores_optimum)

num_runs_per_scaling = 3

# Find filenames for each run
for cores in num_cores_default:
    for run in range(num_runs_per_scaling):
        for filename in file_list_default:
            if filename[0:int(32 + len(str(cores)) + len(str(run)))] == \
                'timings_strong_scaling_omp_' + str(cores) + '_run_' + str(run):
                file_timings_default.append(filename)

for cores in num_cores_no_ht:
    for run in range(num_runs_per_scaling):
        for filename in file_list_no_ht:
            if filename[0:int(32 + len(str(cores)) + len(str(run)))] == \
                'timings_strong_scaling_omp_' + str(cores) + '_run_' + str(run):
                file_timings_no_ht.append(filename)

for cores in num_cores_ec2:
    for run in range(num_runs_per_scaling):
        for filename in file_list_ec2:
            if filename[0:int(32 + len(str(cores)) + len(str(run)))] == \
                'timings_strong_scaling_omp_' + str(cores) + '_run_' + str(run):
                file_timings_ec2.append(filename)

for cores in num_cores_optimum:
    for run in range(num_runs_per_scaling):
        for filename in file_list_optimum:
            if filename[0:int(32 + len(str(cores)) + len(str(run)))] == \
                'timings_strong_scaling_omp_' + str(cores) + '_run_' + str(run):
                file_timings_optimum.append(filename)

print("Found ", len(file_timings_default), " default file(s).")
print("Found ", len(file_timings_no_ht), " no HT file(s).")
print("Found ", len(file_timings_ec2), " ec2 file(s).")
print("Found ", len(file_timings_optimum), " optimum file(s).")

# Load files
timings_default = []
timings_no_ht = []
timings_ec2 = []
timings_optimum = []

for filename in file_timings_default:
    timings_default.append(np.load(path_default + filename, allow_pickle=True))
for filename in file_timings_no_ht:
    timings_no_ht.append(np.load(path_no_ht + filename, allow_pickle=True))
for filename in file_timings_ec2:
    timings_ec2.append(np.load(path_ec2 + filename, allow_pickle=True))
for filename in file_timings_optimum:
    timings_optimum.append(np.load(path_optimum + filename, allow_pickle=True))

# Timings
# create=0; start=1; end=2; var=3;
N1 = np.zeros((6, 3))
for j in range(3):
    N1[:,j] = np.array([1,2,4,8,16,24])
N2 = np.zeros((5, 3))
for j in range(3):
    N2[:,j] = np.array([1,2,4,8,10])

job_time_default = np.zeros((num_scalings_default, num_runs_per_scaling))
container_times_default = np.zeros((num_scalings_default, num_runs_per_scaling))
python_time_default = np.zeros((num_scalings_default, num_runs_per_scaling))
devito_time_default = np.zeros((num_scalings_default, num_runs_per_scaling))
kernel_time_default = np.zeros((num_scalings_default, num_runs_per_scaling))

job_time_no_ht = np.zeros((num_scalings_no_ht, num_runs_per_scaling))
container_times_no_ht = np.zeros((num_scalings_no_ht, num_runs_per_scaling))
python_time_no_ht = np.zeros((num_scalings_no_ht, num_runs_per_scaling))
devito_time_no_ht = np.zeros((num_scalings_no_ht, num_runs_per_scaling))
kernel_time_no_ht = np.zeros((num_scalings_no_ht, num_runs_per_scaling))

python_time_ec2 = np.zeros((num_scalings_ec2, num_runs_per_scaling))
devito_time_ec2 = np.zeros((num_scalings_ec2, num_runs_per_scaling))
kernel_time_ec2 = np.zeros((num_scalings_ec2, num_runs_per_scaling))

python_time_optimum = np.zeros((num_scalings_optimum, num_runs_per_scaling))
devito_time_optimum = np.zeros((num_scalings_optimum, num_runs_per_scaling))
kernel_time_optimum = np.zeros((num_scalings_optimum, num_runs_per_scaling))


# creation (0), start (1), stop (2), gradient_timestamp (3), python_runtime (4), devito_runtime (5), 2*3 kernel times (6-11)
idx = 0
for j in range(num_scalings_default):
    for k in range(num_runs_per_scaling):
        T = timings_default[idx]
        job_time_default[j, k] = (T[3] - T[0])/1e3
        container_times_default[j, k] = (T[2] - T[1])/1e3
        python_time_default[j, k] = T[4]
        devito_time_default[j, k] = T[5]
        kernel_time_default[j, k] = np.sum(T[6:])
        idx += 1

idx = 0
for j in range(num_scalings_no_ht):
    for k in range(num_runs_per_scaling):
        T = timings_no_ht[idx]
        job_time_no_ht[j, k] = (T[3] - T[0])/1e3
        container_times_no_ht[j, k] = (T[2] - T[1])/1e3
        python_time_no_ht[j, k] = T[4]
        devito_time_no_ht[j, k] = T[5]
        kernel_time_no_ht[j, k] = np.sum(T[6:])
        idx += 1

idx = 0
for j in range(num_scalings_ec2):
    for k in range(num_runs_per_scaling):
        T = timings_ec2[idx]
        python_time_ec2[j, k] = T[1]
        devito_time_ec2[j, k] = T[0]
        kernel_time_ec2[j, k] = np.sum(T[2:])
        idx += 1

idx = 0
for j in range(num_scalings_optimum):
    for k in range(num_runs_per_scaling):
        T = timings_optimum[idx]
        python_time_optimum[j, k] = T[1]
        devito_time_optimum[j, k] = T[0]
        kernel_time_optimum[j, k] = np.sum(T[2:])
        idx += 1

# Speedups T1/TnPython
t1_default = np.mean(devito_time_default[0,:])
t2_default = np.mean(kernel_time_default[0,:])
speedup1_default = t1_default / devito_time_default
speedup2_default = t2_default / kernel_time_default

t1_no_ht = np.mean(devito_time_no_ht[0,:])
t2_no_ht = np.mean(kernel_time_no_ht[0,:])
speedup1_no_ht = t1_no_ht / devito_time_no_ht
speedup2_no_ht = t2_no_ht / kernel_time_no_ht

t1_ec2 = np.mean(devito_time_ec2[0,:])
t2_ec2 = np.mean(kernel_time_ec2[0,:])
speedup1_ec2 = t1_ec2 / devito_time_ec2
speedup2_ec2 = t2_ec2 / kernel_time_ec2

t1_optimum = np.mean(devito_time_optimum[0,:])
t2_optimum = np.mean(kernel_time_optimum[0,:])
speedup1_optimum = t1_optimum / devito_time_optimum
speedup2_optimum = t2_optimum / kernel_time_optimum

# Speedup
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.set_xscale("log", nonposx='clip')
#ax.set_yscale("log", nonposy='clip')
ax.errorbar(num_cores_default[0:6], np.mean(speedup2_default[0:6,:]/N1, axis=1), fmt='o-', capsize=4)
ax.errorbar(num_cores_no_ht[0:6], np.mean(speedup2_no_ht[0:6,:]/N1, axis=1), fmt='D-', capsize=4)
ax.errorbar(num_cores_no_ht[0:6], np.mean(speedup2_ec2[0:6,:]/N1, axis=1), fmt='s-', capsize=4)
ax.errorbar(num_cores_optimum[0:5], np.mean(speedup2_optimum[0:5,:]/N2, axis=1), fmt='v-', capsize=4)
#ax.yaxis.set_major_formatter(NullFormatter())
#ax.yaxis.set_minor_formatter(NullFormatter())
plt.xticks(np.array([1,2,4,8,10,16,24]), ('1', '2', '4', '8', '10', '16', '24'), size=10)
#plt.yticks(np.array([1,2,4,8]), ('1', '2', '4', '8'), size=10)
ax.set_xlabel('No. of cores', fontsize=10)
ax.set_ylabel('Parallel efficieny', fontsize=10)
ax.set_ylim([0.01, 1.1])
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
plt.legend(['Batch default', 'Batch no HT', 'EC2 metal', 'Optimum'], loc='lower left', fontsize=9)
plt.tight_layout()
savefig('strong_scaling_omp_speedup.png', dpi=600, format='png')

# Kernel runtimes
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.errorbar(num_cores_default[0:6], np.mean(kernel_time_default[0:6,:], axis=1), fmt='o-', capsize=4)
ax.errorbar(num_cores_no_ht[0:6], np.mean(kernel_time_no_ht[0:6,:], axis=1), fmt='D-', capsize=4)
ax.errorbar(num_cores_no_ht[0:6], np.mean(kernel_time_ec2[0:6,:], axis=1), fmt='s-', capsize=4)
ax.errorbar(num_cores_optimum[0:5], np.mean(kernel_time_optimum[0:5,:], axis=1), fmt='v-', capsize=4)
ax.set_xlabel('No. of cores', fontsize=10)
ax.set_ylabel('Devito kernel runtime [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.set_ylim([200, 2999])
ax.yaxis.set_major_formatter(NullFormatter())
ax.yaxis.set_minor_formatter(NullFormatter())
plt.xticks(np.array([1,2,4,8,10,16,24]), ('1', '2', '4', '8', '10', '16', '24'), size=10)
plt.yticks(np.array([250, 500, 1000, 2000]), ('250', '500', '1000', '2000'), size=10)
plt.legend(['Batch default', 'Batch no HT', 'EC2 metal', 'Optimum'], loc='upper right', fontsize=9)
plt.tight_layout()
savefig('strong_scaling_omp_times.png', dpi=600, format='png')

plt.show()
