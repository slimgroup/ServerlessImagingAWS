
# Docker

The required Docker images for the workflow are publicly available on Docker hub. The Docker image used by AWS Batch is specified in the job parameter files of the numerical examples (e.g. `~/ServerlessImagingAWS/numerical_examples/imaging_example_sgd/parameters.json`). In the current set up, all single-node batch jobs use the pre-existing Docker image `aws_seismic_imaging:v1.0`. To (optionally) obtain a local copy of the image, run:

```
docker pull philippwitte/aws_seismic_imaging:v1.0
```

All multi-node batch jobs use the per-exisiting Docker image `aws_seismic_imaging_mpi:v1.0`. Obtain an (optional) local copy with:

```
docker pull philippwitte/aws_seismic_imaging_mpi:v1.0
```

To reproduce the numerical examples, no actions regarding Docker are necessary.

## Single-node batch jobs

To update or modify the Docker container for single node batch jobs, first pull the current version of the image with the above command. Update the Dockerfile in `~/ServerlessImagingAWS/docker/single_node_batch` as desired and then rebuild the Docker image with a new tag (e.g. `v1.1`):

```
cd ~/ServerlessImagingAWS/docker/single_node_batch
docker build -t aws_seismic_imaging:tag .
```

As users cannot store their modified images on the original `philippwitte` Docker hub, you will upload the new image to your AWS account. First, you need to obtain login credentials by AWS. Copy-paste the output of the following command back into the terminal:

```
# Get ECR login credentials and use the token that is printed in the terminal
aws ecr get-login --no-include-email
```

If the log in was successful, you will see the message "Login Succeeded" in your terminal. Next, create a repository on AWS called `aws_seismic_imaging`:

```
# Create repository (only first time)
aws ecr create-repository --repository-name aws_seismic_imaging
```

Now, tag the new image using the URI of the repository that you just created. To find the URI of your repository, go to the AWS console -> `Services` -> `ECR` -> `aws_seismic_imaging`. Tag your image by running:

```
# tag image
docker tag aws_seismic_imaging:tag URI:tag
```

Finally, upload your Docker image to your AWS container registry:

```
docker push URI:tag
```

Note the full name of your new image (`URI:tag`) and update the job parameter files correspondingly.


## Multi-node batch jobs

Updating or modifying the Docker image for multi-node AWS Batch jobs follows the same steps as the previous instructions. Namely, modify the Dockerfile in `~/ServerlessImagingAWS/docker/multi_node_batch` and rebuild the image using a new tag (e.g. `v1.1`)

```
cd ~/ServerlessImagingAWS/docker/multi_node_batch
docker build -t aws_seismic_imaging_mpi:tag .
```

Tag the image, obtain the AWS ECR log-in credentials and push it to the ECR by following the steps from above. (Replace all instances of `aws_seismic_imaging` in the instructions with `aws_seismic_imaging_mpi`.)
