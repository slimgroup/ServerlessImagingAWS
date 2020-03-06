# An event-driven approach to serverless seismic imaging in the cloud


This documentation describes how to set up the workflow described in the paper "An event-driven approach to serverless seismic imaging in the cloud". The documentation also provides instructions how to reproduce the numerical examples and performance tests. Setting up the following seismic imaging workflow requires an Amazon Web services (AWS) account. To reproduce the workflow, follow the instructions of this documentation step-by-step. Please do not leave out any steps, as this will result in a malfunctioning workflow.

**Disclaimer**: Some of the services and instance types used for the examples are not available as part of the AWS free tier and will invoke charges


## Necessary AWS credentials

The steps for reproducing the workflow require access to the **IAM user name** and password (to log into the AWS console), as well as to the **AWS Access Key ID** and the **AWS Secret Access key**.

## Install and configure AWS Command Line Interface

The first required step is the installation of the AWS command line interface (CLI). With `pip3`, the CLI can be installed from a Linux/Unix terminal by executing the following command:

```
pip3 install awscli --upgrade --user
```

Once installed, the CLI must be configured with the AWS user credentials. Run `aws configure` from the command line and enter your AWS Access Key ID, the AWS Secret Access Key and a region name (e.g. `us-east-1`).


## Clone github repository

Next, clone the Github repository that contains all setup scripts and the numerical examples. Here, we add the repository to the home directory (`~/`):

```
git clone https://github.com/slimgroup/ServerlessImagingAWS ~/.
```
