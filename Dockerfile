FROM ubuntu:20.04

ARG IMAGE_ID

ENV BACKUP_PROOF_IMAGE=$IMAGE_ID

RUN apt-get  update && apt-get install less lsb-release vim wget openssh-client cron rsyslog python3-pip libssl-dev libacl1-dev mysql-client -yqq
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt && rm /tmp/requirements.txt

ADD python_backup_proof /python_backup_proof
RUN cd /python_backup_proof && pip3 install -e ./

ADD scripts/verify_* /usr/local/bin/
RUN chmod +x /usr/local/bin/verify_*

#RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
#RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | tee  /etc/apt/sources.list.d/pgdg.list
#RUN apt-get install postgresql-client-12 -yqq


