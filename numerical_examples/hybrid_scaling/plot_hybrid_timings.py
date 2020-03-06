import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick

# Load timings
cwd = os.getcwd()
path = cwd + '/results/'
file_list = os.listdir(path)

file_timings_omp_small_24 = []
file_timings_omp_large_24 = []
file_timings_omp_large_48 = []
file_timings_hybrid_large_48 = []
num_runs_per_scaling = 3

# Find filenames for each run
for filename in file_list:
    if filename[0:38] == 'timings_hybrid_RESTRICT_num_threads_24':
        file_timings_omp_small_24.append(filename)
    if filename[0:35] == 'timings_hybrid_FALSE_num_threads_24':
        file_timings_omp_large_24.append(filename)
    if filename[0:35] == 'timings_hybrid_FALSE_num_threads_48':
        file_timings_omp_large_48.append(filename)
    if filename[0:34] == 'timings_hybrid_TRUE_num_threads_24':
        file_timings_hybrid_large_48.append(filename)

# Load files (3 files per example, each 6 values: Submission, Start, End, Devito, Python, Kernel)
timings_omp_small_24 = []
timings_omp_large_24 = []
timings_omp_large_48 = []
timings_hybrid_large_48 = []

for filename in file_timings_omp_small_24:
    timings_omp_small_24.append(np.load(path + filename))
for filename in file_timings_omp_large_24:
    timings_omp_large_24.append(np.load(path + filename))
for filename in file_timings_omp_large_48:
    timings_omp_large_48.append(np.load(path + filename))
for filename in file_timings_hybrid_large_48:
    timings_hybrid_large_48.append(np.load(path + filename))

T1 = np.zeros(shape=(num_runs_per_scaling, 6))
T2 = np.zeros(shape=(num_runs_per_scaling, 6))
T3 = np.zeros(shape=(num_runs_per_scaling, 6))
T4 = np.zeros(shape=(num_runs_per_scaling, 6))

for j in range(num_runs_per_scaling):
    T1[j, :] = timings_omp_small_24[j]
    T2[j, :] = timings_omp_large_24[j]
    T3[j, :] = timings_omp_large_48[j]
    T4[j, :] = timings_hybrid_large_48[j]


# Kernel times
kernel = np.zeros(shape=(4,2))
kernel[0,0] = np.mean(T1[:,5])
kernel[1,0] = np.mean(T2[:,5])
kernel[2,0] = np.mean(T3[:,5])
kernel[3,0] = np.mean(T4[:,5])
kernel[0,1] = np.std(T1[:,5])
kernel[1,1] = np.std(T2[:,5])
kernel[2,1] = np.std(T3[:,5])
kernel[3,1] = np.std(T4[:,5])


# Timings plot
fig, ax = plt.subplots(figsize=(3, 3))
num_cores = np.array([1,2,3,4])
bar1 =  ax.bar(num_cores[0:1], kernel[0:1,0], yerr=kernel[0:1,1], align='center', alpha=0.8, ecolor='black', width=.4, capsize=3)
bar2 =  ax.bar(num_cores[1:], kernel[1:,0], yerr=kernel[1:,1], align='center', alpha=0.8, ecolor='black', width=.4, capsize=3)
plt.xticks(num_cores, ('24', '24', '48', '48'), size=8)
ax.set_xlabel('Total no. of CPU cores', fontsize=8)
ax.set_ylabel('Devito kernel runtime [s]', fontsize=8)
ax.tick_params(axis='y', labelsize=8)
ax.tick_params(axis='x', labelsize=8)
ax.set_ylim([0, 500])

plt.legend(['1,911 x  5,394 grid points', '1,911 x 10,789 grid points'], loc='upper right', fontsize=8)


def autolabel(rects, labels):
    """
    Attach a text label above each bar displaying its height
    """
    i=0
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 10, labels[i],
            ha='center', va='bottom', fontsize=8, fontweight='bold', rotation=90, color='white')
        i+=1

labels1 = ['OpenMP']
labels2 = ['OpenMP', 'OpenMP', 'OpenMP + MPI']
autolabel(bar1, labels1)
autolabel(bar2, labels2)
plt.tight_layout()
savefig('hybrid_scaling.png', dpi=300, format='png')
plt.show()
