FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG IMAGE_ID

ENV BACKUP_PROOF_IMAGE=$IMAGE_ID

RUN apt-get  update && apt-get install curl build-essential aptitude apt-rdepends net-tools software-properties-common ca-certificates rsync less lsb-release vim wget openssh-client openssh-server sshpass cron rsyslog python3 python3-dev python3-venv python3-pip libssl-dev libacl1-dev jq -yqq && \
    rm -rf /var/lib/apt/lists/*

RUN rm -rf /tmp/docker-ce-cli && mkdir /tmp/docker-ce-cli && cd /tmp/docker-ce-cli && \
    curl --output cli-jammy.tar.gz https://code.parsehub.com/p/phfiles/raw/docker/docker-ce/27.2.1/cli-jammy.tar.gz && \
    tar xvzf cli-jammy.tar.gz && \
    dpkg -i docker-ce-cli_*.deb && \
    dpkg -i docker-buildx-plugin_*.deb docker-compose-plugin_*.deb && \
    rm -rf /tmp/docker-ce-cli

COPY requirements.txt /tmp/
ADD python_backup_proof /python_backup_proof
ADD scripts/verify_* /usr/local/bin/
ADD scripts/borg-env /usr/local/bin/

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install -r /tmp/requirements.txt && rm /tmp/requirements.txt

RUN cd /python_backup_proof && pip3 install -e ./

RUN chmod +x /usr/local/bin/verify_*

RUN chmod +x /usr/local/bin/borg-env
