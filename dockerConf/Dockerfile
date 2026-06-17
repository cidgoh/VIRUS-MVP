FROM python:3.12

ARG WORKDIR=/home/ubuntu/VIRUS-MVP

WORKDIR ${WORKDIR}

COPY . .

# Copy docker CLI binary
COPY --from=docker:20.10 /usr/local/bin/docker /usr/local/bin/docker

RUN mkdir -p cache_directory \
    && mkdir -p .local/bin \
    && apt-get update -y \
    && apt-get install -y \
        openjdk-21-jre \
        curl \
        wget \
        procps \
    && wget -qO .local/bin/nextflow https://github.com/nextflow-io/nextflow/releases/download/v23.10.0/nextflow-23.10.0-all \
    && chmod +x .local/bin/nextflow \
    && python3 -m venv venv \
    && ./venv/bin/pip install --upgrade pip wheel \
    && ./venv/bin/pip install "setuptools<81" \
    && ./venv/bin/pip install -r requirements.txt \
    && sed -i 's/\r$//g' ./dockerConf/start.sh \
    && chmod +x ./dockerConf/start.sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
# Add local binaries and venv binaries to PATH
ENV PATH="${WORKDIR}/.local/bin:${WORKDIR}/venv/bin:${PATH}"

ENTRYPOINT ["./dockerConf/start.sh"]

EXPOSE 8050