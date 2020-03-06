#!/bin/bash
aws ec2 request-spot-instances --instance-count $1 --launch-specification file://spot_instances_parameters.json
