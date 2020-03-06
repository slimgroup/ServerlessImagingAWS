import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick
import pdb


####################################################################################################

def create_schedule(interruption_times, batchsize, num_fails):
    # Create interruption schedule as function of failure percentage:
    failure_perc = np.linspace(start=0, stop=.5, num=num_fails)
    num_runs = len(failure_perc)
    schedule = np.zeros(shape=(num_runs, batchsize))
    for j in range(num_runs):
        num_failures = int(batchsize * failure_perc[j])
        idx = np.random.permutation(batchsize)[0:num_failures]
        schedule[j, idx] = interruption_times[0:num_failures]
    return schedule, failure_perc

def model_runtimes(container_times, schedule, restart=True, restart_time=120):

    num_runs, batchsize = schedule.shape
    runtime_event = np.zeros(num_runs)

    for run in range(num_runs):
        # Model runtimes for given failure schedule
        work = []
        for j in range(batchsize):
            work.append(container_times[j])
        instances = np.zeros(batchsize)

        tic=0
        shut_downs = np.copy(schedule[run, :])
        while True:

            # Schedule work if available
            if len(work) > 0:
                for j in range(len(work)):
                    # Find instance with least amount of assigned work
                    idx = np.argmin(instances)
                    instances[idx] += work.pop()

            # increase timer by 1 second
            tic += 1

            rm = []
            for j in range(len(instances)):
                if shut_downs[j] <= tic and shut_downs[j] > 0:
                    if restart is True:
                        instances[j] += restart_time + shut_downs[j]
                        shut_downs[j] = 0
                    else:
                        work.append(instances[j])   # add work back to list
                        rm.append(j)    # collect entries to be removed

            if len(rm) > 0:
                instances = np.delete(instances, rm)    # remove instance
                shut_downs = np.delete(shut_downs, rm)

            if tic >= np.max(instances):
                break
        runtime_event[run] = np.max(instances)
    return runtime_event

####################################################################################################

# Model resilience for saving in memory or w/ opt. checkpointing
case = 'memory'
#case = 'checkpointing'

# Load timings w/o interruptions
path = os.getcwd()
if case == 'memory':
    T = np.load(path + '/timings_memory.dat')
else:
    T = np.load(path + '/timings_checkpointing.dat')
batchsize = T.shape[0]

container_times = (T[:,2] - T[:,1])/1e3
print("Average container runtime: ", np.mean(container_times))

# 100 random interruption times
tmin = 1
tmax = np.max(container_times)
num_failures = 20
num_runs = 10
spot_price = 0.2874/60/60
resilience_restart = np.zeros(shape=(num_runs, num_failures))
resilience_no_restart = np.zeros(shape=(num_runs, num_failures))
cost_restart = np.zeros(shape=(num_runs, num_failures))
cost_no_restart = np.zeros(shape=(num_runs, num_failures))

for j in range(num_runs):
    print("Model run ", j, " of ", num_runs)
    interruption_times = np.random.randint(low=tmin, high=tmax, size=batchsize)
    schedule, failure_percentage = create_schedule(interruption_times, batchsize, num_failures)

    # Model runtimes
    runtime_retry = model_runtimes(container_times, schedule, restart=True, restart_time=60)
    runtime_no_retry = model_runtimes(container_times, schedule, restart=False)

    resilience_restart[j, :] = runtime_retry[0] / runtime_retry
    resilience_no_restart[j, :] = runtime_no_retry[0] / runtime_no_retry

    cost_restart[j, :] = runtime_retry*spot_price
    cost_no_restart[j, :] = runtime_no_retry*spot_price

r1 = np.mean(resilience_restart, axis=0)
e1 = np.std(resilience_restart, axis=0)
r2 = np.mean(resilience_no_restart, axis=0)
e2 = np.std(resilience_no_restart, axis=0)
x = failure_percentage*100

c1 = np.mean(cost_restart, axis=0)
c2 = np.mean(cost_no_restart, axis=0)

fig, ax1 = plt.subplots(figsize=(3.33, 3))
ax1.plot(x, r1, color='#1B2ACC')
ax1.fill_between(x, r1-e1, r1+e1, alpha=0.5, edgecolor='#1B2ACC', facecolor='#089FFF')
ax1.plot(x, r2, color='#CC4F1B')
ax1.fill_between(x, r2-e2, r2+e2, alpha=0.5, edgecolor='#CC4F1B', facecolor='#FF9848')
ax1.set_xlabel('Percentage of instance failures', fontsize=8)
ax1.set_ylabel('Resilience factor', fontsize=8)
ax1.tick_params(axis='y', labelsize=8)
ax1.tick_params(axis='x', labelsize=8)
plt.legend(['w/ instance restart', 'w/o instance restart'], fontsize=8)
plt.tight_layout()

if case == 'memory':
    savefig('resilience_save_in_memory.png', dpi=300, format='png')
else:
    savefig('resilience_save_in_checkpointing_2.png', dpi=300, format='png')
