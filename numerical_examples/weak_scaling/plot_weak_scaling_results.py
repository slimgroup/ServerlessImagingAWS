import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick

# Load timings
cwd = os.getcwd()
path = cwd + '/results/'

file_list = os.listdir(path)

file_timings = []
instance_no = np.array([1, 2, 4, 8, 16, 32, 64, 128])
num_scalings = len(instance_no)
num_runs_per_scaling = 10

for batchsize in instance_no:
    for run in range(num_runs_per_scaling):
        for filename in file_list:
            if filename[0:int(23 + len(str(batchsize)) + len(str(run)))] == \
                'timings_batchsize_' + str(batchsize) + '_run_' + str(run):
                file_timings.append(filename)

print("Found ", len(file_timings), " file(s).")
timings = []
for filename in file_timings:
    timings.append(np.load(path + filename))

# Timings
# create=0; start=1; end=2; var=3;
job_time = np.zeros((num_scalings, num_runs_per_scaling))
container_time = np.zeros((num_scalings, num_runs_per_scaling))
container_time_err = np.zeros((num_scalings, num_runs_per_scaling))
reduction_time = np.zeros((num_scalings, num_runs_per_scaling))

# Cost
cost = np.zeros((num_scalings, num_runs_per_scaling))
spot_price_per_hour = 0.2748  # m4.4xlarge (10:11 AM EDT, 4/5/2019, Region US-East/N. Virginia)
spot_price_per_sec = spot_price_per_hour / 60 / 60

idx = 0
for j in range(num_scalings):
    for k in range(num_runs_per_scaling):
        T = timings[idx]

        t1 = (T[:,3] - T[:,0]) / 1e3
        job_time[j, k] = np.mean(t1)

        t2 = (T[:,2] - T[:,1]) / 1e3
        container_time[j, k] = np.mean(t2)
        container_time_err[j, k] = np.std(t2)
        cost[j, k] = np.sum(t2) / instance_no[j] * spot_price_per_sec

        t3 = np.abs((T[:,3] - T[:,2]) / 1e3)
        reduction_time[j, k] = np.min(t3, axis=0)

        idx += 1
#95: 1.96
def confidence_interval(x, z=1.645):
    x_mean = np.mean(x, axis=1)
    x_std = np.std(x, axis=1)
    n_sqrt = np.sqrt(x.shape[1])
    return z*x_std / n_sqrt

# Full time-to-solution and its individual components
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.bar(np.log(instance_no), np.mean(job_time, axis=1), yerr=confidence_interval(job_time), align='center', alpha=0.8, ecolor='black', width=.3, capsize=3)
ax.bar(np.log(instance_no), np.mean(container_time, axis=1), yerr=confidence_interval(container_time), align='center', alpha=0.8, ecolor='black', width=.3, capsize=3)
ax.bar(np.log(instance_no), np.mean(reduction_time, axis=1), yerr=confidence_interval(reduction_time), align='center', alpha=0.8, ecolor='black', width=.3, capsize=3)
plt.xticks(np.log(instance_no), ('1', '2', '4', '8', '16', '32', '64', '128'))
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Time-to-solution [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.set_ylim([0, 1000])
plt.legend(['Full job', 'Container', 'Reduction'], fontsize=9)
plt.tight_layout()
savefig('weak_scaling_gradients.png', dpi=300, format='png')

# Average startup time
startup_times = job_time - container_time - reduction_time
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.bar(np.log(instance_no), np.mean(startup_times, axis=1), yerr=confidence_interval(startup_times), align='center', alpha=0.8, ecolor='black', width=.3, capsize=3)
plt.xticks(np.log(instance_no), ('1', '2', '4', '8', '16', '32', '64', '128'))
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Average startup time [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
plt.tight_layout()
savefig('job_runtime_first.png', dpi=300, format='png')

# Average container runtime and cost
fig, ax1 = plt.subplots(figsize=(3.66, 3))
ax1.set_xlabel('No. of instances', fontsize=10)
ax1.set_ylabel('Average container runtime [s]', fontsize=10)
ax1.bar(np.log(instance_no), np.mean(container_time, axis=1), yerr=confidence_interval(container_time), align='center', alpha=0.8, ecolor='black', width=.32, capsize=3, color='white')
ax1.tick_params(axis='y', labelsize=10)
ax1.tick_params(axis='x', labelsize=10)
axx1 = gca()
ax1.set_ylim([0, axx1.get_ylim()[1]*1.15])

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
ax2.set_ylabel('Total cost [$]', fontsize=10)
ax2.bar(np.log(instance_no), np.mean(cost, axis=1), yerr=confidence_interval(cost), align='center', alpha=0.8, ecolor='black', width=.32, capsize=3)
ax2.bar(np.log(instance_no), np.mean(cost, axis=1), yerr=confidence_interval(cost), align='center', alpha=0.8, ecolor='black', width=.32, capsize=3)
plt.xticks(np.log(instance_no), ('1', '2', '4', '8', '16', '32', '64', '128'))
ax2.tick_params(axis='y', labelsize=10)
fig.tight_layout()  # otherwise the right y-label is slightly clipped
axx2 = gca()
ax2.set_ylim([0, axx2.get_ylim()[1]*1.15])
savefig('container_runtime_cost.png', dpi=300, format='png')

# Plot additional reduction time
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.bar(np.log(instance_no), np.mean(reduction_time, axis=1), yerr=confidence_interval(reduction_time), align='center', alpha=0.8, ecolor='black', width=.3, capsize=3, color='green')
plt.xticks(np.log(instance_no), ('1', '2', '4', '8', '16', '32', '64', '128'))
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Additional reduction time [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
plt.tight_layout()
savefig('reduction_runtime_mean.png', dpi=300, format='png')

plt.show()
