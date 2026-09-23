FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        python3.12 \
        python3.12-venv \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash ubuntu || true

USER ubuntu
WORKDIR /home/ubuntu
