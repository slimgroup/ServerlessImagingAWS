import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick
from cycler import cycler

# Load timings
cwd = os.getcwd()
path_r5 = cwd + '/results/run_r5_max_cpu/'
path_c5n = cwd + '/results/run_c5n_max_cpus/'
file_list_r5 = os.listdir(path_r5)
file_list_c5n = os.listdir(path_c5n)

file_timings_r5 = []
file_timings_c5n = []
num_instances = np.array([1,2,4,8,16])
num_scalings = len(num_instances)
num_runs_per_scaling = 3

for batchsize in num_instances:
    for run in range(num_runs_per_scaling):
        for filename in file_list_r5:
            if filename[0:int(23 + len(str(batchsize)) + len(str(run)))] == \
                'timings_num_nodes_' + str(batchsize) + '_run_' + str(run):
                file_timings_r5.append(filename)
        for filename in file_list_c5n:
            if filename[0:int(23 + len(str(batchsize)) + len(str(run)))] == \
                'timings_num_nodes_' + str(batchsize) + '_run_' + str(run):
                file_timings_c5n.append(filename)

print("Found ", len(file_timings_r5), " R5 file(s).")
print("Found ", len(file_timings_c5n), " C5n file(s).")

timings_r5 = []
timings_c5n = []

for filename in file_timings_r5:
    timings_r5.append(np.load(path_r5 + filename))    # timings: list of num_files entries: 1 x 6

for filename in file_timings_c5n:
    timings_c5n.append(np.load(path_c5n + filename))

# Timings
# create=0; start=1; end=2; var=3; devito=4; script=5
job_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
container_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
kernel_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
devito_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
script_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))

job_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
container_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
kernel_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
devito_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
script_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))

idx = 0
for j in range(num_scalings):
    for k in range(num_runs_per_scaling):
        T = timings_r5[idx].reshape(7)
        job_runtime_r5[j,k] = (T[2] - T[0]) / 1e3
        container_runtime_r5[j,k] = (T[2] - T[1]) / 1e3
        kernel_runtime_r5[j,k] = T[4] / num_instances[j]
        devito_runtime_r5[j,k] = T[5]
        script_runtime_r5[j,k] = T[6]

        T = timings_c5n[idx].reshape(7)
        job_runtime_c5n[j,k] = (T[2] - T[0]) / 1e3
        container_runtime_c5n[j,k] = (T[2] - T[1]) / 1e3
        kernel_runtime_c5n[j,k] = T[4] / num_instances[j]
        devito_runtime_c5n[j,k] = T[5]
        script_runtime_c5n[j,k] = T[6]

        idx += 1


# Timings plot
fig, ax = plt.subplots(figsize=(3.33, 3))
#ax.set_xscale("log", nonposx='clip')
#ax.set_yscale("log", nonposy='clip')
bar1 = ax.bar(np.log(num_instances), np.mean(container_runtime_r5, axis=1), align='edge', alpha=0.8, ecolor='black', width=-.2, capsize=3)
bar2 =  ax.bar(np.log(num_instances), np.mean(container_runtime_c5n, axis=1), align='edge', alpha=0.8, ecolor='black', width=.2, capsize=3)
plt.xticks(np.log(num_instances), ('1', '2', '4', '8', '16'), size=10)
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Devito kernel runtime [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.set_ylim([0, 500])
plt.legend(['r5 family', 'c5n family'], loc='upper right', fontsize=9)

def autolabel(rects, labels, scale):
    """
    Attach a text label above each bar displaying its height
    """
    i=0
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/scale, 10, labels[i],
            va='bottom', fontsize=9, rotation=90, color='white')
        i+=1

labels_r5 = ['r5.12xlarge (24)', 'r5.4xlarge (16)', 'r5.2xlarge (16)', 'r5.xlarge (16)', 'r5.large (16)']
labels_c5n = ['c5n.18xlarge (18)', 'c5n.9xlarge (36)', 'c5n.4xlarge (32)', 'c5n.2xlarge (32)', 'c5n.xlarge (32)']
autolabel(bar1, labels_c5n, 1.15)
autolabel(bar2, labels_r5, 7)

plt.tight_layout()
savefig('strong_scaling_runtime_max_threads.png', dpi=300, format='png')

# Cost r5 vs c5n
# Cost plot (N. Virigina, May 13, 2019, 10:04 PM)
r5_on_demand = np.array([3.024, 1.008, 0.504, 0.252, 0.126])/60/60    # r5.12xlarge, r5.4xlarge, r5.2xlarge, r5.xlarge, r5.large
r5_spot = np.array([0.8766, 0.2959, 0.1491, 0.0732, 0.0356])/60/60

c5n_on_demand = np.array([3.888, 1.944, 0.864, 0.432, 0.216])/60/60    # c5n.18xlarge, c5n.9xlarge, c5n.4xlarge, c5n.2xlarge, c5n.xlarge
c5n_spot = np.array([1.1659, 0.583, 0.2591, 0.1295, 0.0648])/60/60

r5_on_demand_price = np.zeros((num_scalings, num_runs_per_scaling))
r5_spot_price = np.zeros((num_scalings, num_runs_per_scaling))
c5n_on_demand_price = np.zeros((num_scalings, num_runs_per_scaling))
c5n_spot_price = np.zeros((num_scalings, num_runs_per_scaling))

for j in range(num_runs_per_scaling):
    r5_on_demand_price[:,j] = num_instances * container_runtime_r5[:,j] * r5_on_demand
    r5_spot_price[:,j] = num_instances * container_runtime_r5[:,j] * r5_spot
    c5n_on_demand_price[:,j] = num_instances * container_runtime_c5n[:,j] * c5n_on_demand
    c5n_spot_price[:,j] = num_instances * container_runtime_c5n[:,j] * c5n_spot
r5_spot_price[1:] = 0  # only supported for single instances
c5n_spot_price[1:] = 0  # only supported for single instances

fig, ax = plt.subplots(figsize=(3.33, 3))
custom_cycler = (cycler('color',['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']))  # blue, organge, green, red
ax.set_prop_cycle(custom_cycler)
ax.bar(np.log(np.array([1,2,4,8,16])), np.mean(r5_on_demand_price, axis=1), align='edge', alpha=0.8, ecolor='black', width=-.2, capsize=3)
ax.bar(np.log(np.array([1,2,4,8,16])), np.mean(r5_spot_price, axis=1), align='edge', alpha=0.8, ecolor='black', width=-.2, capsize=3)
ax.bar(np.log(np.array([1,2,4,8,16])), np.mean(c5n_on_demand_price, axis=1), align='edge', alpha=0.8, ecolor='black', width=.2, capsize=3)
ax.bar(np.log(np.array([1,2,4,8,16])), np.mean(c5n_spot_price, axis=1), align='edge', alpha=0.8, ecolor='black', width=.2, capsize=3)

plt.xticks(np.log(np.array([1,2,4,8,16])), ('1', '2', '4', '8', '16'))
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Cost per gradient [$]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.set_ylim([0, .5])
plt.legend(['r5 on-demand', 'r5 spot', 'c5n on-demand', 'c5n spot', ], fontsize=9)
plt.tight_layout()
savefig('strong_scaling_cost_max_thread.png', dpi=300, format='png')

plt.show()
