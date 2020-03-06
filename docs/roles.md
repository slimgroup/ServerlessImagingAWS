
# IAM roles

AWS manages access to its services through *roles*. Users and AWS services such as Lambda functions require explicit permissions to interact with other services or to request computational resources. *User roles* provide permissions to a specific IAM user, while *service roles* allow specific AWS services to interact with each other. For example, to start an AWS Batch job from the command line, users require the `AWSBatchFullAccess` user role. If we want to allow a container launched by AWS Batch to send messages to an SQS queue, we need to provide an AWS service role for AWS Batch and attach the `AmazonSQSFullAccess` policy to it. The following instructions create the necessary user and service roles for our workflow.

## User roles

Log into the AWS console (<https://console.aws.amazon.com/console>) and check if the following roles are attached to your user in `Services` -> `IAM` -> `Users` -> `your_user_name`. Run the following commands in a terminal to obtain the missing permissions that are not attached to your account so far. (Replace `your_user_name` by your IAM user name).


```
# EC2
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AmazonEC2FullAccess

# Batch
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AWSBatchFullAccess

# ECR
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

# Lambda
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AWSLambdaFullAccess     

# SQS
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AmazonSQSFullAccess

# Step Functions
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess

# S3 Read
aws iam attach-user-policy --user-name your_user_name --policy-arn \
    arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```


## Service roles

The following service roles are required for the workflow:

1. `AWSBatchServiceRole`

Check if the role exists in your AWS console under *IAM* -> *Roles*. If not, open a terminal in the current directory (`~/aws_workflow`) and run the following commands:

```
# Create role
aws iam create-role --role-name AWSBatchServiceRole  \
    --assume-role-policy-document file://service_roles/create_AWSBatchServiceRole.json \
    --description "Allows Batch to create and manage AWS resources on your behalf."

# Attach policy
aws iam attach-role-policy --role-name AWSBatchServiceRole --policy-arn \
    arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole
```

2. ` StepFunctionsLambdaRole`

Check if the role exists in *IAM* -> *Roles*. If not, open a terminal in the current directory (`~/cloud-imaging`) and run the following commands:

```
# Create role
aws iam create-role --role-name StepFunctionsLambdaRole  \
    --assume-role-policy-document file://service_roles/create_StepFunctionsLambdaRole.json \
    --description "Allows Step Functions to access AWS resources on your behalf."

# Attach policy
aws iam attach-role-policy --role-name StepFunctionsLambdaRole --policy-arn \
    arn:aws:iam::aws:policy/service-role/AWSLambdaRole
```

3. `SLIM-Extras_ECS_for_EC2`

Create this role, regardless of whether any other ECS roles exist so far:

```
# Create role
aws iam create-role --role-name SLIM-Extras_ECS_for_EC2  \
    --assume-role-policy-document file://service_roles/create_SLIM-Extras_ECS_for_EC2.json \
    --description "Allows EC2 instances in an ECS cluster to access ECS."

# Attach policies
aws iam attach-role-policy --role-name SLIM-Extras_ECS_for_EC2 --policy-arn \
    arn:aws:iam::aws:policy/AmazonSQSFullAccess

aws iam attach-role-policy --role-name SLIM-Extras_ECS_for_EC2 --policy-arn \
    arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy --role-name SLIM-Extras_ECS_for_EC2 --policy-arn \
    arn:aws:iam::aws:policy/IAMReadOnlyAccess

aws iam attach-role-policy --role-name SLIM-Extras_ECS_for_EC2 --policy-arn \
    arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role
```

4. `SLIM-Extras_for_Lambda`

Create this role, regardless of whether any other Lambda roles exist so far:

```
# Create role
aws iam create-role --role-name SLIM-Extras_for_Lambda \
    --assume-role-policy-document file://service_roles/create_SLIM-Extras_for_Lambda.json \
    --description "Allows Lambda functions to call AWS services on your behalf."

# Attach policies
aws iam attach-role-policy --role-name SLIM-Extras_for_Lambda --policy-arn \
    arn:aws:iam::aws:policy/AmazonSQSFullAccess

aws iam attach-role-policy --role-name SLIM-Extras_for_Lambda --policy-arn \
    arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy --role-name SLIM-Extras_for_Lambda --policy-arn \
    arn:aws:iam::aws:policy/AWSLambdaFullAccess

aws iam attach-role-policy --role-name SLIM-Extras_for_Lambda --policy-arn \
    arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# Create and attach specialized Lambda for Batch policy
aws iam create-policy --policy-name LambdaBatchExecutionPolicy \
    --policy-document file://service_roles/create_LambdaBatchExecutionPolicy.json\
    --description "Allow Lambda to access AWS Batch services including job registration and submission."

aws iam attach-role-policy --role-name SLIM-Extras_for_Lambda \
    --policy-arn arn:aws:iam::851065145468:policy/LambdaBatchExecutionPolicy
```

5. Roles for using Spot instances with Batch

Create the following roles to enable spot instances for usage with Batch:

```
# AmazonEC2SpotFleetRole
aws iam create-role --role-name AmazonEC2SpotFleetRole --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Sid":"","Effect":"Allow","Principal":{"Service":"spotfleet.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

# AWSServiceRoleForEC2Spot
aws iam create-service-linked-role --aws-service-name spot.amazonaws.com

# AWSServiceRoleForEC2SpotFleet
aws iam create-service-linked-role --aws-service-name spotfleet.amazonaws.com
```
