# Preparations before execution

Reproducing the numerical examples and performance tests requires uploading the BP 2004 velocity model and data set to your S3 account. First, download the velocity model, the mask for the water bottom and the data set (7.4 GB) from the Georgia Tech FTP server:

```
cd ~/ServerlessImagingAWS/numerical_examples
wget ftp://slim.gatech.edu/data/users/pwitte/models/bp_synthetic_2004_velocity.h5
wget ftp://slim.gatech.edu/data/users/pwitte/models/bp_synthetic_2004_water_bottom.h5
wget ftp://slim.gatech.edu/data/users/pwitte/data/bp_synthetic_2004.tar.gz
```

Extract the seismic data with `tar -xzvf bp_synthetic_2004.tar.gz` in the current directory. The models and the data need to be uploaded to an S3 bucket. Check if any pre-existing buckets are available in the AWS console -> `Services` -> `S3`. If not, create a new bucket, such as `slim-bucket-common` (we will use this bucket name in the instructions, but you can choose a different name).

We will upload the models to S3 with some meta data attached to it, to specify the grid spacing and origin. The script `~/ServerlessImagingAWS/numerical_examples/upload_files_to_s3.py` automatically does this and uploads the models and data to S3. Before running this script, open it and fill in your S3 bucket name and the paths where you want to store the models. Follow this naming convention:

 - paths for velocity and water model: `your_user_name/models`

 - seismic data: `your_user_name/data/`

Update the script and run it from the directory into which you downloaded the data from the FTP server. Uploading the data will take a while, as there are 1,348 files to upload. Check whether the files have been uploaded successfully in the AWS console ->` Services` -> `S3` -> `bucket-name`.


# Reproducing the examples

Reproducing the numerical examples involves uploading the Python scripts of our application to S3. During runtime, the AWS Batch workers will fetch the script from S3 and run it to compute the gradients. Most examples do not involve running the full workflow, i.e. they do not require executing the AWS Step Function state machine. Instead, the `launch_test.py` scripts invoke the scaling tests for as single iteration of stochastic gradient descent (SGD), by manually triggering the Lambda function that is responsible for submitting the AWS Batch jobs. The `launch_tests.py` scripts also automatically collect the kernel and container run times from AWS and save them for plotting.

Each example directory contains a job parameter file called `parameters.json`. Users are required to fill in the missing entries in each file, such as bucket names and the correct S3 paths.

# Weak Scaling

The scripts for reproducing the weak scaling example are located in `~/ServerlessImagingAWS/numerical_examples/weak_scaling`.

1) First, upload the Python script `bp_synthetic_weak_scaling.py` to S3. Use the AWS console in the browser to upload the file or use the command line interface:

```
aws s3 cp bp_synthetic_weak_scaling.py s3://bucket-name/user-name/scripts/bp_synthetic_weak_scaling.py
```

2) The job parameters are specified in `parameters.json`. Fill in the following missing entries:

- `bucket_name`: name of your S3 bucket.

- `partial_gradient_path`: S3 path where partial gradients will be stored. The path name must follow the naming convention `user_name/bp_partial_gradients/`. It is important **not** to omit the final `/` in the path name.

- `full_gradient_path`: S3 path name for full gradients. Naming convention: `user_name/bp_full_gradients/`

- `model_path`: S3 paths in which models are stored. Naming convention: `user_name/models/`

- `variable_path`: S3 paths in which images are stored. Naming convention: `user_name/bp_variables/`

- `script_path`: S3 paths in which Python script is stored. Naming convention: `user_name/scripts/`

- `data_path`: S3 path in which the seismic data is stored. Naming convention: `user_name/data/`

- optional: `container`. Specifies the Docker image for AWS Batch. If you modified the Docker image and uploaded it to your AWS account, replace with the full name of the new Docker image (i.e. the image URI plus the tag).

Do not modify the existing entries.


3) To compute the gradient of the BP model for a given batch size, run the `launch_test.py` script with the batch size and the run number as input arguments. The script invokes the `ComputeGradients` Lambda function to submit the AWS Batch job for the gradient computations. The script then waits until the job has finished, the gradient summation is completed and the updated image is written to the S3 bucket. The script collects all timings automatically from AWS and writes the results to a pickle file. Execute the following commands to run the example for a batch size of 2:

```
export BATCHSIZE=2
export RUN_ID=0
python launch_test $BATCHSIZE $RUN_ID
```

4) To reproduce all weak scaling timings from the manuscript, run the shell script `./run_timings.sh`, which executes the `launch_test.py` script for a batch size ranging from `1` to `128`. The script runs three consecutive timings per batch size and waits 700 seconds in between runs to ensure that AWS Batch has enough time to shut down all EC2 instances. Otherwise, AWS Batch uses already running instances in the consecutive timings and the time it takes AWS Batch to launch the EC2 instances is not accounted for.

5) Once all timings have been completed, the `plot_weak_scaling_results.py` script can be used to re-generate the figures from the manuscript. The original timings that are plotted in the manuscript are available in the `results` directory. Running the plotting script will create the figures using these timings.


# Stochastic gradient descent example

To reproduce the full SGD example and run the Step Functions workflow for 30 iterations, follow the subsequent steps. All scripts for the examples are located in the `~/ServerlessImagingAWS/numerical_examples/imaging_example_sgd` directory.

1) Upload the script `bp_synthetic_sgd.py` to `Services` -> `S3` -> `your-bucket` -> `user-name` -> `scripts` (either using the AWS console or using the CLI as in the previous example).

2) All job parameters are specified in `parameters.json`. Fill in all missing entries, following the naming conventions as in the above "Weak scaling" example. Do not modify existing entries.

3) In this example, we execute the full Step Functions state machine, not just a Lambda function to compute a single SGD iteration. Start the Step Functions workflow by running the following command from within the `~/ServerlessImagingAWS/numerical_examples/imaging_example_sgd` directory. First find the ARN of your state machine in the AWS console -> `Step Functions` -> `LSRTM-SGD` and then insert it into the following command:

```
aws stepfunctions start-execution \
    --state-machine-arn   arn:aws:states:us-east-1:xxxxxxxxxxxx:stateMachine:LSRTM-SGD \
    --input file://parameters.json
```

4) You can check the status of your workflow in the AWS console and get live updates of which task of the workflow is currently being executed. Go to the console -> `Services` -> `Step Functions` -> `LSRTM-SGD` and find the latest run in the `Executions` window

5) After the execution of the workflow has finished, re-create the seismic imaging from the manuscript with the script `plot_final_image.py`.


# Strong scaling with OpenMP

Scripts for the OpenMP strong scaling examples are located in `~/ServerlessImagingAWS/numerical_examples/strong_scaling`.

1) Upload the script `bp_synthetic_omp_scaling_batch.py` to `Services` -> `S3` -> `your-bucket` -> `user-name` -> `scripts`

2) Fill in the missing entries of the job parameter file `parameter.json`. Follow the naming convention from before and do not modify existing entries.

3) To reproduce the timings with AWS Batch, either run the Python script `launch_test.py` for a single run or run the shell script `run_timings_batch.sh` to reproduce all timings (3 runs each).

4) To reproduce the timings on an EC2 bare metal instances, manually request a `r5.metal` instance from the AWS console -> `Services` -> `EC2` -> `Launch Instance`. Ensure that ssh access to the instance is allowed by providing the corresponding security group. Once the instance is running, connect to the instance via ssh:

```
ssh -i ~/.ssh/user_key_pair.pem -o StrictHostKeyChecking=no -l ubuntu public_DNS_of_instance

```

On the instance, install git, clone the software repository and install all required packages:

```
sudo apt-get update
sudo apt-get install git-core
git clone https://github.gatech.edu/pwitte3/aws_workflow
cd aws_workflow/numerical_examples/strong_scaling
./setup.sh
```

For the bare metal examples, there are no json parameter files. Instead, parameters are hard-coded into the main script `bp_synthetic_omp_scaling_bare_metal.py`. Before running the example, open the script and fill in the missing S3 paths that point to the models and seismic data.

Run the timings using the shell script `run_timings_bare_metal.sh`:

```
source ~/.bashrc
./run_timings_bare_metal.sh
```

5) All figures from the manuscript can be re-generated with the Python script `plot_omp_timings.py`.


# Strong scaling with MPI

Scripts for the MPI strong scaling examples are located in `~/ServerlessImagingAWS/numerical_examples/strong_scaling_mpi`.

1) Upload the scripts `bp_synthetic_mpi_scaling.py` and `bp_synthetic_single.py` to `Services` -> `S3` -> `your-bucket` -> `user-name` -> `scripts`

2) Fill in the missing entries of the job parameter file `parameter.json` and `parameter_single.json`. The latter is the parameter file for running the application as on a single node. Follow the naming convention from before and do not modify existing entries. The `parameter.json` parameter file has one additional required field:

- `user_id`: Your AWS account number. This 12 digit number can be found in `Services` -> `IAM` or in the top-right corner of the AWS console.

The parameter files are set up for running the timings on `r5.24xlarge` instances. To run the timings on `c5n.18xlarge` instances, change the following entries in the json parameter files:

 - `batch_queue`: `MultiNodeQueue_C5N_MAX_18`

 - `instance_type`: `c5n.18xlarge`

 - `omp_num_threads`: `18`


3) To reproduce the strong scaling examples with MPI, either run the Python script `launch_test.py` for a single run or run the shell scripts `run_timings.sh` and `run_timings_single.sh` to reproduce all timings (3 runs each).

4) After reproducing the timings, generate the plots from the manuscript by running the script `plot_mpi_strong_scaling.py` and `plot_mpi_strong_scaling_var.py`.


# Hybrid example

Scripts for the hybrid OpenMP-MPI examples are located in `~/ServerlessImagingAWS/numerical_examples/hybrid_scaling`.

1) Upload the scripts `bp_synthetic_hybrid.py` and `bp_synthetic_omp.py` to `S3` -> `your-bucket` -> `user-name` -> `scripts`

2) Fill in the missing entries of the job parameter file `parameter.json`. Follow the naming convention from before and do not modify existing entries.

3) To reproduce the timings, run the Python script `launch_test.py` for a single run or the shell script `run_timings.sh` to reproduce all timings (3 runs each).

4) After reproducing the timings, print the timings from the Table with the Python script `print_kernel_times.py`. To generate the plot, run the script `plot_hybrid_timings.py`.


# Cost examples

Scripts for the cost comparison and cost saving strategies are located in `~/ServerlessImagingAWS/numerical_examples/cost`.

1) Upload the script `bp_synthetic_cost.py` to `S3` -> `your-bucket` -> `user-name` -> `scripts`

2) Fill in the missing entries of the job parameter file `parameter.json`. Follow the naming convention from before and do not modify existing entries.

3) To reproduce the timings for the cost comparisons, run the python script `launch_test.py`. The script computes a gradient of the BP model for a batch size of `100` and saves the runtimes as a pickle file.

4) To plot the cost comparison from the manuscript, run the Python script: `plot_cost_comparison.py`.

5) To plot the cost saving strategies for spot instances, use the following Python scripts:

- `plot_cost_zone_c5n.py`: compare zones for the `c5n` instance.

- `plot_cost_zone_c1.py`: compare zones for the `c1` instance.

- `plot_cost_type.py`: compare different instances types within the `us-east-1c` zone.

The scripts can automatically fetch the historic spot prices from AWS for a specified time period. However, historic spot prices are only available for a period of three months, so we provide For this reason, the historic spot prices shown in the manuscript are saved as pickle files. The above scripts.


# Resilience

Scripts for the resilience example are located in `~/ServerlessImagingAWS/numerical_examples/resilience`.


1) Upload the script `bp_synthetic_cost.py` to `S3` -> `your-bucket` -> `user-name` -> `scripts`

2) Fill in the missing entries of the job parameter file `parameter.json`. Follow the naming convention from before and do not modify existing entries.

3) The script `launch_test.py` can be used to compute the gradient for the BP model for a given batch size and percentage of instance failures. To obtain the timings for a batch size of 100 and without failures (failure rate = 0), run:

```
python launch_test.py 100 0 0`.
```

where the first argument is batch size, the second argument is the run number and the third argument is the failure rate. To compute the gradient with 50 percent of the instances failing at random times during the run, type:

```
python launch_test.py batch_size 0 0.5`.
```

The timings from the manuscript for an increasing number of instance failures are modeled using the timings without instance failures and a two minute penalty for instance restarts. However, the script can be used to verify that the actual runtime with instance failures is predicted correctly by our model.

4) To re-create the figures from the manuscript and plot the results, run the Python script `plot_resilience_modeled.py`
