
# Batch environment

To run AWS Batch jobs, we need to first set up *Compute environments* and *Job queues*. The compute environments essentially specify the virtual cluster that AWS Batch has access to. This involves specifying which type of instances are allowed, as well as their size (i.e. number of CPUs and memory). For multi-node AWS Batch jobs, we also have to set up a shared file system and a customized Amazon Machine Image (AMI).

## Elastic file system

Setting up an elastic file system is only necessary for **multi-node batch jobs**, i.e. for AWS Batch jobs that run each job on multiple  EC2 instances. For **single-node batch jobs**, skip this part and proceed to the next section.

For multi-node AWS Batch jobs, we need to set up a shared file system called *elastic file system* (EFS). Furthermore, we need to set up a customized Amazon Machine Image (AMI) and mount the shared file system. Detailed instructions for these steps are provided in the AWS documentation: <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_efs.html>. Here, we provide a summary of the necessary steps:

1) Create an elastic file system by logging into the AWS console in the web browser and go to `Services` -> `EFS` -> `Create file system`. By default, AWS will fill in all available subnets and include the default security group. For each zone, also add the SSH-security group. Proceed to step 2 and 3 and then select `Create File System`.

2) Next, we have to modify the AMI that is used by AWS Batch and mount the file system. For this, we launch an EC2 instances with the ECS-optimized AMI, mount the EFS and create a custom AMI, which will then be used in the compute environment.

Choose the Amazon Linux 2 AMI for your region from the following list:
<https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html>. For example, for the `us-east-1` region, this is AMI ID `ami-0fac5486e4cff37f4`. Click on `Launch Instance` to request an EC2 instance with the corresponding AMI. Using the `t2.micro` instance type is sufficient for this task. Next, connect to your instance via `ssh`:

```
ssh -Y -i ~/.ssh/user_key_pair -o StrictHostKeyChecking=no -l ec2-user public_DNS_of_instance
```

Once you are logged into the instance, following the subsequent steps:

- Create mount point: `sudo mkdir /efs`

- Install the amazon-efs-utils client software: `sudo yum install -y amazon-efs-utils`

- Make a backup of the `/etc/fstab` file: `sudo cp /etc/fstab /etc/fstab.bak`

- Open the original file with `sudo vi /etc/fstab` and add the following line to it. Replace `efs_dns_name` with the DNS name of your elastic file system (find the DNS name in the AWS console -> `Services` -> `EFS` -> `name-of-your-file-system` -> `DNS name`):

```
efs_dns_name:/ /efs nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0

```

- Reload file system: `sudo mount -a`

- Validate that file system is mounted correctly: `mount | grep efs`


Log out from the instance and create a new AMI from the running EC2 instance. Go the list of running EC2 instances in the AWS console and select your running instance -> `Actions` -> `Image` -> `Create Image`. Choose an image name and then hit `Create Image`.


## AMIs without hyper-threading

By default, AWS Batch uses hyperthreading (HT) on the underlying EC2 instances. For our workflow, we need to disable HT and limit the number of cores to half the number of virtual CPU cores on the corresponding EC2 instance. For example, the `r5.24xlarge` instance has 96 virtual CPUs and therefore 48 physical cores. To disable HT for this instance, we need to set the maximum number of allowed CPUs to 48.

To disable HT, we modify the AMI that is used by AWS Batch. For this, we launch an EC2 instances with the ECS-optimized AMI, specify the maximum number of allowed CPUs and create a custom AMI. This AMI will then be used in the compute environment.

If you already created an AMI in the previous section with an elastic file system, start a new EC2 instance using this AMI and connect to your instance. If you have not created an AMI yet, choose the Amazon Linux 2 AMI for your region from the following list:
<https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html>. For example, for the `us-east-1` region, this is AMI ID `ami-0fac5486e4cff37f4`. Click on `Launch Instance` to request an EC2 instance with the corresponding AMI. Using the `t2.micro` instance type is sufficient for this task. Next, connect to your instance via `ssh`:

```
ssh -Y -i ~/.ssh/user_key_pair -o StrictHostKeyChecking=no -l ec2-user public_DNS_of_instance
```

Open the grub config file with `sudo vi /etc/default/grub` and add `nr_cpus=48` to the line starting with `GRUB_CMDLINE_LINUX` (or however many cores are required). Apply the changes by running:

```
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

Log out from the instance and create a new AMI from the running EC2 instance. Go the list of running EC2 instances in the AWS console and select your running instance -> `Actions` -> `Image` -> `Create Image`. Choose an image name that indicates the maximum number of cores and then hit `Create Image`.

Follow the same steps to create customized AMIs for other instance types with a differet number of CPU cores. E.g. for the `r5.12xlarge` instance, set `nr_cpus=24`, as this instance type has 48 vCPUs with 24 physicsal cores. For the `c5n.18xlarge` instance (72 vCPUs), set `nr_cpus=36` and so on. **Important**: To reproduce the numerical examples, create a total of 4 AMIs: one with a maximum of 8 cores, one with 24 cores, one with 18 cores and one with 48 cores. For multi-node batch jobs, always start the above process from the AMI that has the mounted elastic file system. Otherwise, start from the Amazon Linux 2 AMI.


## Create environments

The performance tests in the manuscript are carried out on several different compute environments. Most examples are run in the `M4_SPOT_MAXCPU_8` environment, using `m4.4xlarge` Spot instances with 8 physical cores per instance. The compute environment can be set up from the command line, with all parameters being specified in the `~/ServerlessImagingAWS/batch/create_environment_m4_spot.json` file. Open the file and fill in **all missing entries**. These are:

 - `spotIamFleetRole`: Go to the AWS console -> `Services` -> `IAM` -> `Roles` and find the `AmazonEC2SpotFleetRole`. Copy the role ARN and paste it.

 - `subnets`:  Find your subnets in the AWS console at `Services` -> `VPC` -> `Subnets`. Copy the Subnet ID of each subnet into the parameter file (separated by commas).

 - `securityGroupIds`: Find the security groups in the console at `Services` -> `EC2` -> `Security groups`. Copy-paste the Group ID of the default security group. To enable ssh access to instances of AWS Batch jobs, optionally create and add an SSH security group to this list.

 - `ec2KeyPair`: To connect to running instances via ssh, add the name of your AWS ssh key pair.

 - `imageId`: Go to the console -> `Services` -> `EC2` -> `AMIs` and find the AMI that was created in the previous step. For the `M4_SPOT_MAXCPU_8` compute environment, find the AMI with 8 cores and copy-paste the AMI-ID into the parameter file.

 - `instanceRole`: Go to the AWS console -> `Services` -> `IAM` -> `Roles`. Find the `SLIM-Extras_ECS_for_EC2` role and add its ARN to the parameter file.


 - `serviceRole`: Go to the AWS console -> `Services` -> `IAM` -> `Roles`. Find the `SLIM-AWSBatchServiceRole` role and add its ARN.

Do not modify the parameters that are already filled in. Save the updated file and then run the following command within the `~/ServerlessImagingAWS` directory:

```
# Create environment
aws batch create-compute-environment --cli-input-json file://batch/create_environment_m4_spot.json
```

You can go to the AWS Console in the web browser and move to `Services` -> `AWS Batch` -> `Compute environments` to verify that the environment has been created successfully.

To reproduce the numerical examples and performance tests, fill in the missing entries of the remaining parameter files: `create_environment_r5_spot_24.json` and `create_environment_r5_spot_48.json`. For the former, select the AMI with 24 cores and for the latter the AMI with 48 cores. Then re-run the above command for these parameter files:

```
# Create environment w/ r5.24xlarge instances
aws batch create-compute-environment --cli-input-json file://batch/create_environment_r5_spot_24.json

# Create bybrid OMP-MPI environment w/ r5.24xlarge instances
aws batch create-compute-environment --cli-input-json file://batch/create_environment_r5_spot_48.json
```


## Create queues

For each compute environment, we need to create an AWS Batch Job queue, to which our workflow will submit its work loads. The queue parameter files do not need to be modified, so simply run the following commands from the terminal within the `~/ServerlessImagingAWS` directory:

```
# Job queue M4 environment
aws batch create-job-queue --cli-input-json file://batch/create_queue_m4_spot.json

# Job queue R5 environment (24 cores)
aws batch create-job-queue --cli-input-json file://batch/create_queue_r5_spot_24.json

# Job queue R5 environment (48 cores)
aws batch create-job-queue --cli-input-json file://batch/create_queue_r5_spot_48.json
```


## Multi-node environment and queues

For multi-node AWS Batch jobs we have to set up compute environments similar to the ones as specified above, with the major difference that multi-node batch jobs do not support spot instances. We therefore set up on-demand compute environments for the `r5.24xlarge` and the `c5n.18xlarge` instance type.

The environment parameters are specified in the files `create_environment_r5_multinode_24.json` and `create_environment_c5n_multinode_18.json`. Fill in the missing parameters like in the above example. For the `AMI` field, enter the AMI ID of the AMI with the elastic file system. Use the AMI with a maximum of 24 CPUs for the `r5` environment and the AMI with `18` cores for the `c5n` environment.

The parameter files also specify a placement group called `MPIgroup`. The placement group ensures that EC2 instances of the MPI clusters are in close physical vicinity to each other. Create the `MPIgroup` placement group from the AWS console `Services` -> `EC2` -> `Placement Groups` -> `Create Placement Group`. Enter the name `MPIgroup` and select `Cluster` in the `Strategy` field. Then click the `create` button.

After creating the placement group, generate the compute environments as in the above example:

```
# Create on-demand environment w/ r5.24xlarge instances
aws batch create-compute-environment --cli-input-json file://batch/create_environment_r5_multinode_24.json

# Create on-demand environment w/ c5n.18xlarge instances
aws batch create-compute-environment --cli-input-json file://batch/create_environment_c5n_multinode_18.json
```

Finally, create the corresponding batch queues by running the following commands:

```
# Job queue r5 on-demand
aws batch create-job-queue --cli-input-json file://batch/create_queue_r5_multinode_24.json

# Job queue c5n on-demand
aws batch create-job-queue --cli-input-json file://batch/create_queue_c5n_multinode_18.json
```


## VPC endpoints

For multi-node batch jobs, follow these steps to create endpoints for S3 and SQS in your virtual privat cloud:

 - Log into the AWS console in the browser and go to: `Services` -> `VPC` -> `Endpoints`.

 - Create an S3 endpoint: click `Create Endpoint` and select the S3 service name from the list, e.g. `com.amazonaws.us-east-1.s3`. Next, select the only available route table in the section `Configure route tables`. Finalize the endpoint by clicking the `Create Endpoint` button.

 - Create an SQS endpoint:  click `Create Endpoint`  and select the SQS service name from the list, e.g. `com.amazonaws.us-east-1.sqs`. Ensure that all availability zones are selected. Under `Security group`, select the default security group, as well as the `SSH` group. Finalize the endpoint by clicking the `Create Endpoint` button.
