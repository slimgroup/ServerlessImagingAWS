import h5py, os, subprocess
import matplotlib.pyplot as plt
from CloudExtras import *
import numpy as np

# TO DO: fill in the correct path, bucket name and object paths:
path_to_data = os.getcwd()
bucket = 'slim-bucket-common'   # replace w/ your S3 bucket name
path_models = 'pwitte/models'   # i.e. user_name/models
path_data = 'pwitte/data'       # i.e. user_name/data

# Read models
model = h5py.File(path_to_data + '/bp_synthetic_2004_velocity.h5', 'r+')
m = np.array(model['m'])
o = (0.0, 0.0)
d = (6.25, 6.25)

waterbottom = h5py.File(path_to_data + '/bp_synthetic_2004_water_bottom.h5', 'r+')
wb = np.array(waterbottom['wb'])

# Cast types
m = m.astype('float32')
wb = wb.astype('float32')

# Save to bucket: model_put(model, origin, spacing, bucket, key):
model_put(np.transpose(m), o, d, bucket, path_models + '/bp_synthetic_2004_velocity')
model_put(np.transpose(wb), o, d, bucket, path_models + '/bp_synthetic_2004_water')

# # Upload data
# for file in os.listdir('bp_synthetic_2004'):
#     subprocess.run(['aws', 's3', 'cp', 'bp_synthetic_2004/' + file, 's3://' + bucket + '/' + path_data + '/' + file])
#     print("Uploaded file: ", file)