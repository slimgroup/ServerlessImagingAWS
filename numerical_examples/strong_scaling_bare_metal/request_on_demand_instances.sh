#!/bin/bash

aws ec2 run-instances --count $1 \
    --security-group-ids sg-58967010 sg-0019a9838b4564ae6 \
    --ebs-optimized \
    --iam-instance-profile Name=ec2-on-demand-profile \
    --image-id ami-04b9e92b5572fa0d1 \
    --instance-type r5.metal \
    --key-name philipp_dell \
    --placement AvailabilityZone=us-east-1a,GroupName=MPIgroup \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mpi_bare_metal}]'
