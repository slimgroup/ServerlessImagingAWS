import numpy as np
import matplotlib.pyplot as plt
import boto3, pickle
from datetime import datetime
import matplotlib.dates as mdates

client = boto3.client('ec2')

####################################################################################################
# Auxiliary functions

def get_spot_price(client, time_start, time_end, instance_type=['r5.24xlarge',], zone='us-east-1a', verbose=False):

    response = client.describe_spot_price_history(
        InstanceTypes=instance_type,
        AvailabilityZone=zone,
        StartTime=time_start, # year, month, day, hour, minute, second
        EndTime=time_end,
        ProductDescriptions=['Linux/UNIX',],
    )

    num_prices = len(response['SpotPriceHistory'])
    if verbose is True:
        print("Found ", num_prices, " spot prices")

    if num_prices > 0:
        price = np.zeros(num_prices)
        time = []
        i = 0
        for entry in response['SpotPriceHistory']:
            price[i] =  float(entry['SpotPrice'])
            time.append(entry['Timestamp'])
            i += 1

        return time, price
    else:
        return None, np.inf

def increase_day(month, day):
    if month in [1,3,5,7,8,10,12]:
        num_days = 31
    elif month in [4,6,9,11]:
        num_days = 30
    else:
        num_days = 28
    if day < num_days:
        day +=1
    else:
        if month < 12:
            month += 1
        else:
            month = 1
        day = 1
    return month, day

def increase_timer(month, day, hour, time_per_gradient):
    if hour + time_per_gradient <= 23:
        hour  = hour + time_per_gradient
    else:
        hour = hour + time_per_gradient - 24

        month, day = increase_day(month, day)
    return month, day, hour

###################################################################################################

# If true, download data from aws and save
retrieve_data = False
if retrieve_data is True:
    objects_to_save = []
    f = open('spot_price_type.pckl', 'wb')
else:
    f = open('spot_price_type.pckl', 'rb')
    objects = pickle.load(f)

# ~ data passes
maxiter = 20
batchsize = 100
time_per_gradient = 12  # in hours
zones = 'us-east-1c'

instances = [['m5.xlarge'], ['c5.xlarge'], ['c5n.xlarge'], ['r5.xlarge']]
start_month = 5
start_day = 26
start_hour = 0

day = start_day
hour = start_hour
prices = np.zeros(len(instances))
total_cost = np.zeros(5)

p_prev=0
month = start_month
t_list = []
instance_list = []
for j in range(maxiter):
    print("Iteration: ", j)

    ts = datetime(2019, month, day, hour)

    if retrieve_data is True:
        # Get current spot prices
        for k in range(len(instances)):
            t_curr, p_curr = get_spot_price(client, ts, ts, instance_type=instances[k], zone=zones)
            prices[k] = p_curr
        print(prices)

        # Choose zone/instance type/size
        idx = np.argmin(prices)

        # Save best instance SpotPrice
        instance = instances[idx]
        t_list.append(t_curr)
        instance_list.append(prices[idx])

        print("Use zone: ", instance, " on day ", day, " at time: ", hour)

        month, day, hour = increase_timer(month, day, hour, time_per_gradient)
        total_cost[0] += batchsize*prices[0]*time_per_gradient
        total_cost[1] += batchsize*prices[1]*time_per_gradient
        total_cost[2] += batchsize*prices[2]*time_per_gradient
        total_cost[3] += batchsize*prices[3]*time_per_gradient
        total_cost[4] += batchsize*prices[idx]*time_per_gradient

# Save t_list and prices
if retrieve_data is True:
    objects_to_save.append(t_list)
    objects_to_save.append(instance_list)
    objects_to_save.append(total_cost)
else:
    t_list = objects[0]
    instance_list = objects[1]
    total_cost = objects[2]

# Plot cost comparison
ec2_cost = np.array([0.768, 0.68, 0.864, 0.904])*batchsize*time_per_gradient*maxiter
#p_max = np.max(ec2_cost)
p_max = np.max(total_cost)
total_cost /= p_max
#ec2_cost /= p_max

fig, ax = plt.subplots(figsize=(3.33, 3))
#ax.bar(np.array([1,2,3,4]), ec2_cost, align='edge', ecolor='black', width=-.3)
#ax.bar(np.array([1,2,3,4,5]), total_cost, align='edge', ecolor='black', width=.3)
ax.bar(np.array([1,2,3,4,5]), total_cost, ecolor='black', width=.4)
plt.xticks([1,2,3,4,5], ('m5', 'c5', 'c5n', 'r5', 'best'))
ax.set_xlabel('Instance type', fontsize=8)
ax.set_ylabel('Relative EC2 cost', fontsize=8)
ax.tick_params(axis='y', labelsize=8)
ax.tick_params(axis='x', labelsize=8)
ax.set_ylim([0.75, np.max(total_cost)*1.02])
plt.legend(['us-east-1c'], fontsize=8)
plt.tight_layout()
plt.savefig('figure_cost_types.png', dpi=300, format='png')


# Plot instances prices
ts = datetime(2019, start_month, start_day-1, start_hour+12)
te = datetime(2019, month, day, hour)

if retrieve_data is True:
    time_m5, price_m5 = get_spot_price(client, ts, te, instance_type=instances[0], zone=zones)
    time_c5, price_c5 = get_spot_price(client, ts, te, instance_type=instances[1], zone=zones)
    time_c5n, price_c5n = get_spot_price(client, ts, te, instance_type=instances[2], zone=zones)
    time_r5, price_r5 = get_spot_price(client, ts, te, instance_type=instances[3], zone=zones)

    objects_to_save.append(time_m5); objects_to_save.append(price_m5)
    objects_to_save.append(time_c5); objects_to_save.append(price_c5)
    objects_to_save.append(time_c5n); objects_to_save.append(price_c5n)
    objects_to_save.append(time_r5); objects_to_save.append(price_r5)

else:
    time_m5 = objects[3]; price_m5 = objects[4]
    time_c5 = objects[5]; price_c5 = objects[6]
    time_c5n = objects[7]; price_c5n = objects[8]
    time_r5 = objects[9]; price_r5 = objects[10]

fig, ax = plt.subplots(figsize=(3.33, 3))
plt.plot(time_m5, price_m5, time_c5, price_c5, time_c5n, price_c5n, time_r5, price_r5, t_list, instance_list, '.')
plt.legend(['m5.xlarge', 'c5.xlarge', 'c5n.xlarge', 'r5.xlarge', 'best' ],  fontsize=8)
plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%D')
plt.gca().xaxis.set_major_formatter(myFmt)
ax.set_ylabel('Spot price per hour [$]', fontsize=8)
#plt.xticks([1,2,3,4,5], ('m5', 'c5', 'c5n', 'r5', 'best'))
#plt.locator_params(axis='x', nbins=7)
ax.tick_params(axis='y', labelsize=8)
ax.tick_params(axis='x', labelsize=8)
plt.autoscale(enable=True, axis='x', tight=True)
ax.xaxis.set_major_locator(plt.MaxNLocator(7))
ax.set_ylim([0.068, 0.115])
plt.tight_layout()
plt.savefig('figure_compare_types.png', dpi=300, format='png')

if retrieve_data is True:
    pickle.dump(objects_to_save, f)

plt.show()
