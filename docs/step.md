
# State machine for single-node jobs

The AWS Step Functions workflow is defined as a json file in `~/ServerlessImagingAWS/step_functions/state_machine.json`. The file does not need to be modified. To create the workflow for the first time, run the following command from a terminal within the `~/ServerlessImagingAWS` directory. This step requires the ARN of the Step Functions service role. The ARN can be found in the AWS console -> `Services` -> `IAM` -> `Roles` -> `StepFunctionsLambdaRole`. Copy the ARN and use it in the following command:


```
aws stepfunctions create-state-machine --name LSRTM-SGD \
    --role-arn step_functions_service_role_arn \
    --definition file://step_functions/state_machine.json
```

To upload an updated version of the workflow, first find the ARN of the state machine that we created with the above command. Go to the AWS console -> `Step Functions` -> `LSRTM-SGD` and copy the ARN. Then run the following command using this ARN:

```
aws stepfunctions update-state-machine \
    --state-machine-arn state_machine_arn \
    --definition file://step_functions/state_machine.json
```


# State machine for multi-node jobs

To set up the state-machine for the multi-node workflow, follow the same steps as above. The multi-node workflow is defined in `~/ServerlessImagingAWS/step_functions/state_machine_multinode.json`. Obtain the ARN of the `StepFunctionsLambdaRole` (as described above) and upload the workflow as follows:

```
aws stepfunctions create-state-machine --name LSRTM-SGD-MultiNode \
    --role-arn step_functions_service_role_arn \
    --definition file://step_functions/state_machine_multinode.json
```
