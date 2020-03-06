import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show, xlabel, ylabel, legend, gca, subplot, title, tight_layout, savefig
import matplotlib.ticker as mtick
from matplotlib.ticker import NullFormatter

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

# Container times
container = np.zeros(shape=(4,2))
container[0,0] = np.mean(T1[:,2] - T1[:,1])/1e3
container[1,0] = np.mean(T2[:,2] - T2[:,1])/1e3
container[2,0] = np.mean(T3[:,2] - T3[:,1])/1e3
container[3,0] = np.mean(T4[:,2] - T4[:,1])/1e3
container[0,1] = np.std(T1[:,2] - T1[:,1])/1e3
container[1,1] = np.std(T2[:,2] - T2[:,1])/1e3
container[2,1] = np.std(T3[:,2] - T3[:,1])/1e3
container[3,1] = np.std(T4[:,2] - T4[:,1])/1e3

print("Container runtimes and standard deviation: \n", container)


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

print("Kernel times and standard deviation: \n", kernel)
