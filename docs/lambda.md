# Lambda functions

All AWS Lambda functions used in the workflow are defined in the `~/cloud-imaging/lambda/` directory and each sub-directory contains the source code of the respective Lambda function. Some functions require the installation of additional python packages such as `numpy`. Follow the instructions to create deployment packages for the Lambda functions and to upload them to AWS.

To create and upload the Lambda function, we need the Lambda service role that we created earlier. Log into the AWS console and go to `Services` -> `IAM` -> `Roles` -> `SLIM-Extras_for_Lambda` to find the ARN of this role.


## CreateQueues

From within the `~/cloud-imaging/lambda/CreateQueues` directory, run the following command to create a zip archive:

```
cd ~/cloud-imaging/lambda/CreateQueues
zip -r9 ../CreateQueue.zip .
```

When uploading the function for the first time, run the following command to create a new Lambda function. Replace `copy_paste_role_arn_here` with the ARN of the `SLIM-Extras_for_Lambda` role (see above instructions of how to obtain the ARN):

```
# Upload function
aws lambda create-function --function-name CreateQueues \
    --zip-file fileb://../CreateQueues.zip \
    --runtime python3.6 \
    --timeout 300 \
    --role copy_paste_role_arn_here \
    --handler lambda_function.lambda_handler \
    --memory-size 128
```

If you make changes to the Lambda function and need to update an existing function, first create a new zip file with the above command and then run the following command:

```
# Upload function
aws lambda update-function-code --function-name IteratorStochastic \
    --zip-file fileb://../IteratorStochastic.zip
```


## Iterator

Create the zip archive:

```
cd ~/cloud-imaging/lambda/Iterator
zip -r9 ../Iterator.zip .
```

Create and upload the `Iterator` Lambda function:

```
# Upload function
aws lambda create-function --function-name Iterator \
    --zip-file fileb://../Iterator.zip \
    --runtime python3.6 \
    --timeout 10 \
    --role copy_past_role_arn_here \
    --handler lambda_function.lambda_handler \
    --memory-size 128
```

Update an existing function with a new archive:

```
# Upload function
aws lambda update-function-code --function-name Iterator \
    --zip-file fileb://../Iterator.zip
```

## ComputeGradients

First, install `numpy` and `boto3` inside the `ComputeGradients` directory and create a zip archive. (Lambda functions have `boto3` pre-installed, but the default version is a deprecated version that misses some functionality, so we need to install the current release manually.)

```
cd ~/cloud-imaging/lambda/ComputeGradients
pip install --target . numpy boto3
zip -r9 ../ComputeGradients.zip .
```

Then create and upload the `ComputeGradients` Lambda function:

```
# Upload function
aws lambda create-function --function-name ComputeGradients \
    --zip-file fileb://../ComputeGradients.zip \
    --runtime python3.6 \
    --timeout 900 \
    --role copy_past_role_arn_here \
    --handler lambda_function.gradient_handler \
    --memory-size 128
```

To update an existing function with a new archive, run:

```
# Upload function
aws lambda update-function-code --function-name ComputeGradients \
    --zip-file fileb://../ComputeGradients.zip
```

For multi-node AWS Batch jobs, repeat the above steps for the `ComputeGradients_MultiNode` Lambda function. First create a zip archive called `ComputeGradients_MultiNode.zip` and then run:

```
# Upload multi-node function
aws lambda create-function --function-name ComputeGradients_MultiNode \
    --zip-file fileb://../ComputeGradients_MultiNode.zip \
    --runtime python3.6 \
    --timeout 900 \
    --role copy_past_role_arn_here \
    --handler lambda_function.gradient_handler \
    --memory-size 128
```

## CheckS3ForVariable

Install python packages and create archive:

```
cd ~/cloud-imaging/lambda/CheckS3ForVariable
pip install --target . boto3
zip -r9 ../CheckS3ForVariable.zip .
```

Create and upload Lambda function:

```
# Upload function
aws lambda create-function --function-name CheckS3ForVariable \
    --zip-file fileb://../CheckS3ForVariable.zip \
    --runtime python3.6 \
    --timeout 10 \
    --role copy_past_role_arn_here \
    --handler lambda_function.lambda_handler \
    --memory-size 128
```

Update the function:

```
# Upload function
aws lambda update-function-code --function-name CheckS3ForVariable \
    --zip-file fileb://../CheckS3ForVariable.zip
```

For multi-node AWS Batch jobs, repeat the above steps for the `CheckS3ForVariable_MultiNode` Lambda function. Create a new zip file called `CheckS3ForVariable_MultiNode.zip` and then run:

```
# Upload function
aws lambda create-function --function-name CheckS3ForVariable_MultiNode \
    --zip-file fileb://../CheckS3ForVariable_MultiNode.zip \
    --runtime python3.6 \
    --timeout 10 \
    --role copy_past_role_arn_here \
    --handler lambda_function.lambda_handler \
    --memory-size 128
```

## ReduceGradients

Install python packages and create archive:

```
cd ~/cloud-imaging/lambda/ReduceGradients
pip install --target . numpy boto3
zip -r9 ../ReduceGradients.zip .
```

Create and upload Lambda function:

```
# Upload function
aws lambda create-function --function-name ReduceGradients \
    --zip-file fileb://../ReduceGradients.zip \
    --runtime python3.6 \
    --timeout 60 \
    --role copy_past_role_arn_here \
    --handler lambda_function.lambda_handler \
    --memory-size 512
```

Update the function:

```
# Upload function
aws lambda update-function-code --function-name CheckS3FReduceGradientsorVariable \
    --zip-file fileb://../ReduceGradients.zip
```

## CleanUp

Create archive:

```
cd ~/cloud-imaging/lambda/CleanUp
zip -r9 ../CleanUp.zip .
```

Create and upload Lambda function:

```
# Upload function
aws lambda create-function --function-name CleanUp \
    --zip-file fileb://../CleanUp.zip \
    --runtime python3.6 \
    --timeout 10 \
    --role copy_past_role_arn_here \
    --handler lambda_function.lambda_handler \
    --memory-size 128
```
