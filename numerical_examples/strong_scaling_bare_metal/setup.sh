#!/bin/bash

# Basic packages
sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y iproute2 cmake openssh-server openssh-client python3 python3-pip build-essential gfortran mpich binutils
sudo apt-get install -y vim git-core

# Install EFS utils and mount file system
git clone https://github.com/aws/efs-utils
cd efs-utils
./build-deb.sh
sudo apt-get -y install ./build/amazon-efs-utils*deb
cd ~/
sudo mkdir /efs
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 172.31.88.115:/ /efs

# Install python packages
pip3 install --upgrade --user awscli boto3 segyio
sudo ln -s /home/ubuntu/.local/bin/aws /usr/local/bin/aws

# Download and install devito and dependencies (fixed version from docker)
aws s3 cp s3://slim-bucket-common/pwitte/packages/devito_docker.tar.gz .
tar -xvzf devito_docker.tar.gz
rm devito_docker.tar.gz
mv devito_docker/devito /home/ubuntu/.local/lib/python3.6/site-packages/.
mv devito_docker/devito-3.4+845.gfec640bc.dist-info /home/ubuntu/.local/lib/python3.6/site-packages/.
mv devito_docker/codepy /home/ubuntu/.local/lib/python3.6/site-packages/.
mv devito_docker/codepy-2017.2.2.dist-info /home/ubuntu/.local/lib/python3.6/site-packages/.
mv devito_docker/cgen /home/ubuntu/.local/lib/python3.6/site-packages/.
mv devito_docker/cgen-2018.1.dist-info /home/ubuntu/.local/lib/python3.6/site-packages/.
mv devito_docker/* /home/ubuntu/.
rm -rf devito_docker

# Devito requirements
pip3 install --user -r /home/ubuntu/devito_isotropic/requirements.txt
chmod +x single_run.sh
chmod +x mpi_run.sh
