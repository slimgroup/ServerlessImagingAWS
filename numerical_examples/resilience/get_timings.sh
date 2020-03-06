#!/bin/bash
rm -f ec2_instances.txt
aws ec2 describe-instances --filters Name=instance-type,Values=m4.4xlarge --query 'Reservations[].Instances[].InstanceId' >> ec2_instances.txt
