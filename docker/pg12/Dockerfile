FROM postgres:12-bookworm

RUN apt-get update && \
      apt-get install -yq apt-transport-https less vim psmisc zip unzip wget \
      curl git grep iputils-ping net-tools sudo dnsutils tcptrack build-essential && \
    rm -rf /var/lib/apt/lists

RUN cd / && git clone --depth 1 --branch v1.3.3 https://github.com/tembo-io/pgmq.git
RUN cd pgmq && make && make install
