FROM ubuntu:18.04

# Install packages
#RUN apt-get update
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install -y iproute2 cmake openssh-server openssh-client python3 python3-pip build-essential gfortran mpich
RUN apt-get install -y vim git-core

# Install devito
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade --user git+https://github.com/opesci/devito.git awscli boto3 segyio
RUN ln -s /root/.local/bin/aws /usr/local/bin/aws

# Set up SSH
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN echo "export VISIBLE=now" >> /etc/profile
RUN echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
ENV SSHDIR /root/.ssh
RUN mkdir -p ${SSHDIR}
RUN touch ${SSHDIR}/sshd_config
RUN ssh-keygen -t rsa -f ${SSHDIR}/ssh_host_rsa_key -N ''
RUN cp ${SSHDIR}/ssh_host_rsa_key.pub ${SSHDIR}/authorized_keys
RUN cp ${SSHDIR}/ssh_host_rsa_key ${SSHDIR}/id_rsa
RUN echo " IdentityFile ${SSHDIR}/id_rsa" >> /etc/ssh/ssh_config
RUN echo "Host *" >> /etc/ssh/ssh_config && echo " StrictHostKeyChecking no" >> /etc/ssh/ssh_config
RUN chmod -R 600 ${SSHDIR}/* && \
    chown -R ${USER}:${USER} ${SSHDIR}/
RUN eval `ssh-agent -s` && ssh-add ${SSHDIR}/id_rsa

# Devito requirements
ADD ./devito_isotropic/requirements.txt /app/requirements.txt
RUN pip3 install -U -r /app/requirements.txt
RUN pip3 install -U git+https://github.com/inducer/codepy

# Compiler and Devito environment variables
ENV DEVITO_ARCH="gcc"
ENV DEVITO_MPI="1"
ENV DEVITO_OPENMP="1"
ENV OMP_NUM_THREADS="2"
ENV PYTHONPATH "${PYTHONPATH}:/app/devito_isotropic"
ENV DEVITO_LOGGING="DEBUG"

# Add mpi set-up script and thread pinning script
ADD ./mpi_run.sh /app/mpi_run.sh
ADD ./set_omp_pinning.sh /app/set_omp_pinning.sh
ADD ./send_sqs_msg.py /app/send_sqs_msg.py
RUN chmod 755 /app/mpi_run.sh
RUN chmod 755 /app/set_omp_pinning.sh

# Add application
ADD ./devito_isotropic /app/devito_isotropic

# Run mpi script upon docker launch
EXPOSE 22
WORKDIR /app
CMD ["./mpi_run.sh"]
