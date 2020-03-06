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

# ~ data passes
retrieve_data = False
if retrieve_data is True:
    objects_to_save = []
    f = open('spot_price_c1.pckl', 'wb')
else:
    f = open('spot_price_c1.pckl', 'rb')
    objects = pickle.load(f)

maxiter = 20
batchsize = 100
time_per_gradient = 12  # in hours
zones = ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d']

instance = ['c1.xlarge',]
start_month = 4
start_day = 27
start_hour = 0

day = start_day
hour = start_hour
prices = np.zeros(len(zones))
total_cost = np.zeros(5)

p_prev=0
month = start_month
t_list = []
instance_list = []

for j in range(maxiter):
    print("Iteration: ", j)

    ts = datetime(2019, month, day, hour)

    # Get current spot prices
    if retrieve_data is True:
        for k in range(len(zones)):
            t_curr, p_curr = get_spot_price(client, ts, ts, instance_type=instance, zone=zones[k])
            prices[k] = p_curr
        print(prices)

        # Choose zone/instance type/size
        idx = np.argmin(prices)
        t_list.append(t_curr)
        instance_list.append(prices[idx])
        zone = zones[idx]
        print("Use zone: ", zone, " on day ", day, " at time: ", hour)

        month, day, hour = increase_timer(month, day, hour, time_per_gradient)
        print("Month: ", month, " Day: ", day, " Hour: ", hour)
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
total_cost /= np.max(total_cost)

fig, ax = plt.subplots(figsize=(3.33, 3))
ax.bar(np.array([1,2,3,4,5]), total_cost, align='center', ecolor='black', width=.4)
plt.xticks([1,2,3,4,5], ('1a', '1b', '1c', '1d', 'best'))
ax.set_xlabel('Availability zone', fontsize=8)
ax.set_ylabel('Relative EC2 cost', fontsize=8)
ax.tick_params(axis='y', labelsize=8)
ax.tick_params(axis='x', labelsize=8)
ax.set_ylim([0.75, np.max(total_cost)*1.049])
plt.legend(['c1.xlarge'], fontsize=8)
plt.tight_layout()
plt.savefig('figure_cost_zone_c1.png', dpi=300, format='png')


# Plot instances prices
ts = datetime(2019, start_month, start_day-1, start_hour)
te = datetime(2019, month, day+1, hour)

if retrieve_data is True:
    time_1a, price_1a = get_spot_price(client, ts, te, instance_type=instance, zone='us-east-1a')
    time_1b, price_1b = get_spot_price(client, ts, te, instance_type=instance, zone='us-east-1b')
    time_1c, price_1c = get_spot_price(client, ts, te, instance_type=instance, zone='us-east-1c')
    time_1d, price_1d = get_spot_price(client, ts, te, instance_type=instance, zone='us-east-1d')
    time_1e, price_1e = get_spot_price(client, ts, te, instance_type=instance, zone='us-east-1e')
    time_1f, price_1f = get_spot_price(client, ts, te, instance_type=instance, zone='us-east-1f')

    # Save spot prices (only available from AWS for 3 months)
    objects_to_save.append(time_1a); objects_to_save.append(price_1a)
    objects_to_save.append(time_1b); objects_to_save.append(price_1b)
    objects_to_save.append(time_1c); objects_to_save.append(price_1c)
    objects_to_save.append(time_1d); objects_to_save.append(price_1d)
    objects_to_save.append(time_1e); objects_to_save.append(price_1e)
    objects_to_save.append(time_1f); objects_to_save.append(price_1f)

else:
    time_1a = objects[3]; price_1a = objects[4]
    time_1b = objects[5]; price_1b = objects[6]
    time_1c = objects[7]; price_1c = objects[8]
    time_1d = objects[9]; price_1d = objects[10]
    time_1e = objects[11]; price_1e = objects[12]
    time_1f = objects[13]; price_1f = objects[14]

fig, ax = plt.subplots(figsize=(3.33, 3))
plt.plot(time_1a, price_1a, time_1b, price_1b, time_1c, price_1c, time_1d, price_1d, t_list, instance_list, '.')
plt.legend(['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1f', 'best'],  fontsize=8,  bbox_to_anchor=(0.55, 0.42))
plt.gcf().autofmt_xdate()
myFmt = mdates.DateFormatter('%D')
plt.gca().xaxis.set_major_formatter(myFmt)
ax.set_ylabel('Spot price per hour [$]', fontsize=8)
ax.tick_params(axis='y', labelsize=8)
ax.tick_params(axis='x', labelsize=8)
ax.set_ylim([0.034,0.155])
plt.autoscale(enable=True, axis='x', tight=True)
ax.xaxis.set_major_locator(plt.MaxNLocator(7))
plt.tight_layout()
plt.savefig('figure_compare_zone_c1.png', dpi=300, format='png')

if retrieve_data is True:
    pickle.dump(objects_to_save, f)

plt.show()
