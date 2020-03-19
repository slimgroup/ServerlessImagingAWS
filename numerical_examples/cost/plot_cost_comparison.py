import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick

# Load timings
path = os.getcwd() 
file_list = os.listdir(path)
file_timings = []
for filename in file_list:
    if filename[0:7] == 'timings':
        file_timings.append(filename)
import matplotlib.ticker as mtick
print("Found ", len(file_timings), " file(s).")
timings = []
for filename in file_timings:
    timings.append(np.load(filename, allow_pickle=True))
T = timings[0]
array_size = T.shape[0]

# Plot timings for single gradient w/ given batchsize
f1 = figure(figsize=(1.7, 3))
t_batch = (T[:,2] - T[:,1]) / 1e3   # created: T[:,0]; started: T[:,1]; stopped: T[:,2]
tstart_batch = (T[:,1] - T[:,0]) / 1e3   # created: T[:,0]; started: T[:,1]; stopped: T[:,2]
xaxis = np.arange(1, array_size+1)
plot(xaxis, np.sort(t_batch))
ax = gca()
ax.tick_params(labelsize=10)
ax.set_xlim([1, array_size])
ax.set_ylim([np.min(t_batch)*.9, np.max(t_batch)*1.1])

xlabel('Job ID', fontsize=10)
ylabel('Runtime per gradient [s]', fontsize=10)

tight_layout()
savefig('figure_11a.png', dpi=600, format='png')

####################################################################################################

def model_idle_time(timings, num_nodes, sort=False):
    # Model the time-to-solution to compute workloads given in timings,
    # using a given number of nodes with dynamic scheduling and return
    # the idle time (cumulative time of nodes waiting for last workload)

    if sort is True:
        sorted_timings = np.sort(timings)
        sorted_timings = np.flip(sorted_timings, axis=0)    # sort from largest to smallest
    else:
        sorted_timings = timings

    batchsize = len(timings)
    cum_runtime_per_node = np.zeros(num_nodes)
    for j in range(batchsize):
        idx = np.argmin(cum_runtime_per_node)   # assign workload to node w/ smallest runtime
        cum_runtime_per_node[idx] += sorted_timings[j]

    idle_time = 0
    idx = np.argmax(cum_runtime_per_node)
    for j in range(num_nodes):
        idle_time += (cum_runtime_per_node[idx] - cum_runtime_per_node[j])
    time_to_solution = cum_runtime_per_node[idx]

    return idle_time, time_to_solution

# Compare with running on cluster w/ fixed size (idle time + time to solution)
idle_times_cluster = np.zeros(array_size)
idle_times_batch = np.zeros(array_size) # no idle times w/ batch
time_to_solutions = np.zeros(array_size)

for j in range(array_size):
    idle_times_cluster[j], time_to_solutions[j] = model_idle_time(t_batch, j+1)

# Cost as function of the number of cluster nodes
spot_price_per_hour = 0.2748  # m4.4xlarge (10:11 AM EDT, 4/5/2019, Region US-East/N. Virginia)
spot_price_per_min = spot_price_per_hour / 60

cluster_price = np.zeros(array_size)
batch_price = np.ones(array_size) * np.sum(t_batch) / 60 * spot_price_per_min
for j in range(array_size):
    cluster_price[j] = time_to_solutions[j] / 60 * (j+1) * spot_price_per_min

# Combined plot
fig, ax1 = plt.subplots(figsize=(3.2, 3))

ax1.set_xlabel('No. of instances', fontsize=10)
ax1.set_ylabel('Cumulative idle time [min]', fontsize=10)
ax1.plot(xaxis, idle_times_cluster/60, xaxis, idle_times_batch)#, linewidth=1.)
ax1.tick_params(axis='y', labelsize=10)
ax1.tick_params(axis='x', labelsize=10)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
ax2.set_ylabel('Total cost [$]', fontsize=10)
ax2.plot(xaxis, cluster_price, xaxis, batch_price)#, linewidth=1.)
ax2.tick_params(axis='y', labelsize=10)

legend(['EC2 cluster', 'AWS Batch'], fontsize=9)
ax1.set_xlim([1, array_size])
fig.tight_layout()  # otherwise the right y-label is slightly clipped
savefig('figure_11b.png', dpi=600, format='png')


# Plot runtime as function of the number of cluster nodes
f4 = figure(figsize=(1.7, 3))
plt.semilogy(xaxis, time_to_solutions)#, linewidth=1.)
ax = gca()
ax.tick_params(labelsize=10)
ax.set_xlim([1, array_size])
xlabel('No. of instances', fontsize=10)
ylabel('Time-to-solution [s]', fontsize=10)
tight_layout()
savefig('figure_11c.png', dpi=600, format='png')
show()
