import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick
from cycler import cycler

# Load timings
cwd = os.getcwd()
path_r5 = cwd + '/results/run_r5_24_threads/'
path_r5_metal = cwd + '/results/run_r5_bare_metal/'
path_c5n = cwd + '/results/run_c5n_18_threads/'
path_c5n_metal = cwd + '/results/run_c5n_bare_metal/'
file_list_r5 = os.listdir(path_r5)
file_list_r5_metal = os.listdir(path_r5_metal)
file_list_c5n = os.listdir(path_c5n)
file_list_c5n_metal = os.listdir(path_c5n_metal)

file_timings_r5 = []
file_timings_r5_metal = []
file_timings_c5n = []
file_timings_c5n_metal = []
num_instances = np.array([1,2,4,8,16])
num_scalings = len(num_instances)
num_runs_per_scaling = 3

for batchsize in num_instances:
    for run in range(num_runs_per_scaling):
        for filename in file_list_r5:
            if filename[0:int(23 + len(str(batchsize)) + len(str(run)))] == \
                'timings_num_nodes_' + str(batchsize) + '_run_' + str(run):
                file_timings_r5.append(filename)
        for filename in file_list_r5_metal:
            if filename == 'timings_num_nodes_' + str(batchsize) + '_run_' + str(run):
                file_timings_r5_metal.append(filename)
        for filename in file_list_c5n:
            if filename[0:int(23 + len(str(batchsize)) + len(str(run)))] == \
                'timings_num_nodes_' + str(batchsize) + '_run_' + str(run):
                file_timings_c5n.append(filename)
        for filename in file_list_c5n_metal:
            if filename == 'timings_num_nodes_' + str(batchsize) + '_run_' + str(run):
                file_timings_c5n_metal.append(filename)

print("Found ", len(file_timings_r5), " R5 file(s).")
print("Found ", len(file_timings_r5_metal), " R5.metal file(s).")
print("Found ", len(file_timings_c5n), " C5n file(s).")
print("Found ", len(file_timings_c5n_metal), " R5.metal file(s).")

timings_r5 = []
timings_r5_metal = []
timings_c5n = []
timings_c5n_metal = []

for filename in file_timings_r5:
    timings_r5.append(np.load(path_r5 + filename, allow_pickle=True))    # timings: list of num_files entries: 1 x 6
for filename in file_timings_r5_metal:
    timings_r5_metal.append(np.load(path_r5_metal + filename, allow_pickle=True))
for filename in file_timings_c5n:
    timings_c5n.append(np.load(path_c5n + filename, allow_pickle=True))
for filename in file_timings_c5n_metal:
    timings_c5n_metal.append(np.load(path_c5n_metal + filename, allow_pickle=True))

# Timings
# create=0; start=1; end=2; var=3; devito=4; script=5
job_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
container_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
kernel_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
devito_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))
script_runtime_r5 = np.zeros((num_scalings, num_runs_per_scaling))

kernel_runtime_r5_metal = np.zeros((num_scalings, num_runs_per_scaling))
devito_runtime_r5_metal = np.zeros((num_scalings, num_runs_per_scaling))
script_runtime_r5_metal = np.zeros((num_scalings, num_runs_per_scaling))

job_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
container_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
kernel_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
devito_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))
script_runtime_c5n = np.zeros((num_scalings, num_runs_per_scaling))

kernel_runtime_c5n_metal = np.zeros((num_scalings, num_runs_per_scaling))
devito_runtime_c5n_metal = np.zeros((num_scalings, num_runs_per_scaling))
script_runtime_c5n_metal = np.zeros((num_scalings, num_runs_per_scaling))

idx = 0
for j in range(num_scalings):
    for k in range(num_runs_per_scaling):
        T = timings_r5[idx].reshape(7)
        job_runtime_r5[j,k] = (T[2] - T[0]) / 1e3
        container_runtime_r5[j,k] = (T[2] - T[1]) / 1e3
        kernel_runtime_r5[j,k] = T[4]
        devito_runtime_r5[j,k] = T[5]
        script_runtime_r5[j,k] = T[6]

        T = timings_r5_metal[idx].reshape(3)
        kernel_runtime_r5_metal[j,k] = T[0]
        devito_runtime_r5_metal[j,k] = T[1]
        script_runtime_r5_metal[j,k] = T[2]

        T = timings_c5n[idx].reshape(7)
        job_runtime_c5n[j,k] = (T[2] - T[0]) / 1e3
        container_runtime_c5n[j,k] = (T[2] - T[1]) / 1e3
        kernel_runtime_c5n[j,k] = T[4]
        devito_runtime_c5n[j,k] = T[5]
        script_runtime_c5n[j,k] = T[6]

        T = timings_c5n_metal[idx].reshape(3)
        kernel_runtime_c5n_metal[j,k] = T[0]
        devito_runtime_c5n_metal[j,k] = T[1]
        script_runtime_c5n_metal[j,k] = T[2]

        idx += 1

# Parallel efficieny T1/Tn/n
N = np.zeros((num_scalings, num_runs_per_scaling))
for j in range(num_runs_per_scaling):
    N[:,j] = num_instances

# Kernel time speedups
speedup5_r5 = np.copy(kernel_runtime_r5)
for j in range(3):
    speedup5_r5[:,j] = speedup5_r5[0,j] / speedup5_r5[:,j]
speedup5_r5 = speedup5_r5 / N

speedup5_r5_metal = np.copy(kernel_runtime_r5_metal)
for j in range(3):
    speedup5_r5_metal[:,j] = speedup5_r5_metal[0,j] / speedup5_r5_metal[:,j] 
speedup5_r5_metal /= N

speedup5_c5n = np.copy(kernel_runtime_c5n)
for j in range(3):
    speedup5_c5n[:,j] = speedup5_c5n[0,j] / speedup5_c5n[:,j]
speedup5_c5n = speedup5_c5n / N
speedup5_c5n = np.minimum(speedup5_c5n, np.ones((5,3)))  # shouldn't be > 1

speedup5_c5n_metal = np.copy(kernel_runtime_c5n_metal)
for j in range(3):
    speedup5_c5n_metal[:,j] = speedup5_c5n_metal[0,j] / speedup5_c5n_metal[:,j]
speedup5_c5n_metal /= N


# Parallel efficieny
custom_cycler = (cycler('color',['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']))  # blue, organge, green, red

fig, ax = plt.subplots(figsize=(3.125, 3))
ax.set_xscale("log", nonposx='clip')
#ax.set_yscale("log", nonposy='clip')
ax.set_prop_cycle(custom_cycler)
ax.errorbar(num_instances, np.mean(speedup5_r5, axis=1), fmt='o-', capsize=4)
ax.errorbar(num_instances, np.mean(speedup5_r5_metal, axis=1), fmt='D-', capsize=4)
ax.errorbar(num_instances, np.mean(speedup5_c5n, axis=1), fmt='s-', capsize=4)
ax.errorbar(num_instances, np.mean(speedup5_c5n_metal, axis=1), fmt='v-', capsize=4)
plt.xticks(num_instances, ('1', '2', '4', '8', '16'), size=10)
plt.yticks(np.array([0.2,.4,.6,.8,1.0]), ('0.2','0.4', '0.6', '0.8', '1.0'), size=10)
ax.set_xlabel('No. of EC2 instances', fontsize=10)
ax.set_ylabel('Parallel efficieny', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
#ax.set_xlim([0, 40])
ax.set_ylim([0.15, 1.1])
plt.legend(['r5.24xlarge', 'r5.metal', 'c5n.18xlarge', 'c5n.metal'], loc='lower left', fontsize=9)
plt.tight_layout()
savefig('strong_scaling_mpi_speedup_single_thread.png', dpi=600, format='png')

# Timings plot
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.set_prop_cycle(custom_cycler)
ax.errorbar(num_instances, np.mean(kernel_runtime_r5, axis=1), fmt='o-', capsize=4)
ax.errorbar(num_instances, np.mean(kernel_runtime_r5_metal, axis=1), fmt='D-', capsize=4)
ax.errorbar(num_instances, np.mean(kernel_runtime_c5n, axis=1), fmt='s-', capsize=4)
ax.errorbar(num_instances, np.mean(kernel_runtime_c5n_metal, axis=1), fmt='v-', capsize=4)
plt.xticks(num_instances, ('1', '2', '4', '8', '16'), size=10)
plt.yticks(np.array([50,125,250,500]), ('50','125','250','500'), size=10)
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Devito kernel runtime [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
plt.legend(['r5.24xlarge', 'r5.metal','c5n.18xlarge', 'c5n.metal'], loc='upper right', fontsize=9)
plt.tight_layout()
savefig('strong_scaling_mpi_runtime_single_thread.png', dpi=600, format='png')

# Breakdown of timings c5n
fig, ax = plt.subplots(figsize=(3.33, 3))
ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.set_prop_cycle(custom_cycler)
ax.errorbar(num_instances, np.mean(job_runtime_c5n, axis=1), fmt='o-', capsize=4)
ax.errorbar(num_instances, np.mean(container_runtime_c5n, axis=1), fmt='D-', capsize=4)
ax.errorbar(num_instances, np.mean(script_runtime_c5n, axis=1), fmt='s-', capsize=4)
ax.errorbar(num_instances, np.mean(kernel_runtime_c5n, axis=1), fmt='v-', capsize=4)
plt.xticks(num_instances, ('1', '2', '4', '8', '16'), size=10)
plt.yticks(np.array([50,125,250,500,1000]), ('50','125','250','500','1000'), size=10)
ax.set_xlabel('No. of instances', fontsize=10)
ax.set_ylabel('Runtime [s]', fontsize=10)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.set_ylim([30, 1400])
plt.legend(['Job', 'Container', 'Python', 'Kernel'], fontsize=9)
plt.tight_layout()
savefig('strong_scaling_breakdown_c5n.png', dpi=600, format='png')

# Cost r5 vs c5n
r5_on_demand = 6.048/60/60
r5_spot = 1.7103/60/60

c5n_on_demand = 3.456/60/60
c5n_spot = 1.1659/60/60

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
plt.legend(['r5 on-demand', 'r5 spot', 'c5n on-demand', 'c5n spot'], fontsize=9)
plt.tight_layout()
savefig('strong_scaling_cost_single_thread.png', dpi=600, format='png')

plt.show()
