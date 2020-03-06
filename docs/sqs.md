
# SQS queues

Create an SQS queue for the gradient summation using the following command:

```
aws sqs create-queue --queue-name GradientQueue_1 \
    --attributes DelaySeconds=0,ReceiveMessageWaitTimeSeconds=0,VisibilityTimeout=60
```

Once we have defined the queue, we have to tell the queue which Lambda function to invoke when it is triggered. First, find the ARN of the queue that we just created. Go to the console -> `Simple Queue Service` -> `GradientQueue_1`, copy the ARN and use it in the following command:

```
aws lambda create-event-source-mapping \
    --event-source-arn arn_of_sqs_queue \
    --function-name ReduceGradients
```

You can verify that this trigger was created correctly by clicking on the queue and selecting the `Lambda Triggers` tab at the bottom of the page. The `ReduceGradients` function should be listed as a trigger.

If we run our full worklow by executing the AWS Step Functions state machine, we can specify that we want the SQS queue(s) to be be set up automatically. In this case, set the `auto_create_queues` parameter of the `~/cloud-imaging/numerical_examples/imaging_example_sgd/parameters.json` file to `TRUE`. After executing the workflow, the queue is automatically removed.
