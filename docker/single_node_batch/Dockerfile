FROM ubuntu:18.04

# Install packages
RUN ls
RUN apt-get update
RUN apt install -y python3 python3-pip
RUN apt-get install -y vim git-core cgroup-bin
RUN apt-get install -y openmpi-bin openmpi-common openssh-client openssh-server libopenmpi-dev

# Install devito
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade --user git+https://github.com/opesci/devito.git awscli boto3 segyio
RUN ln -s /root/.local/bin/aws /usr/local/bin/aws

# Devito requirements
ADD ./devito_isotropic/requirements.txt /app/requirements.txt
RUN pip3 install -U -r /app/requirements.txt
RUN pip3 install -U git+https://github.com/inducer/codepy mpi4py

# Compiler and default Devito environment variables
ENV DEVITO_ARCH="gcc"
ENV DEVITO_OPENMP="1"
ENV OMP_NUM_THREADS="2"
ENV PYTHONPATH "${PYTHONPATH}:/app/devito_isotropic"
ENV DEVITO_LOGGING="DEBUG"

# Add mpi set-up script
ADD ./app_run.sh /app/app_run.sh
RUN chmod 755 /app/app_run.sh

# Thread pinning script (disabled by default)
ADD ./set_omp_pinning.sh /app/set_omp_pinning.sh
RUN chmod 755 /app/set_omp_pinning.sh
ENV THREAD_PINNING="FALSE"

# Add application
ADD ./devito_isotropic /app/devito_isotropic

# Run mpi script upon docker launch
EXPOSE 22
WORKDIR /app
CMD ["./app_run.sh"]
