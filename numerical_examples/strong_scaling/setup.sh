#!/bin/bash

# Install packages
sudo apt-get update
sudo apt install -y python3 python3-pip
sudo apt-get install -y vim git-core cgroup-bin

# Install devito
pip3 install --upgrade --user git+https://github.com/opesci/devito.git awscli boto3 segyio
sudo ln -s /root/.local/bin/aws /usr/local/bin/aws

# Devito requirements
pip3 install --user -r /home/ubuntu/code/docker/devito_isotropic/requirements.txt
pip3 install --user git+https://github.com/inducer/codepy

# tkinter
sudo apt-get install -y python3-tk

# Compiler and Devito environment variables
echo "export DEVITO_ARCH=\"gcc\"" >> ~/.bashrc
echo "export DEVITO_OPENMP=\"1\"" >> ~/.bashrc
echo "export OMP_NUM_THREADS=\"2\"" >> ~/.bashrc
echo "export PYTHONPATH=\${PYTHONPATH}:/home/ubuntu/code/docker/devito_isotropic/" >> ~/.bashrc
echo "export DEVITO_LOGGING=\"DEBUG\"" >> ~/.bashrc
echo "export OMP_PLACES=\"\"" >> ~/.bashrc
