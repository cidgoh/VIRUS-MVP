FROM python:latest

ARG WORKDIR

WORKDIR $WORKDIR

COPY . .
COPY --from=docker:20.10 /usr/local/bin/docker .local/bin/

RUN mkdir "cache_directory" \
    && mkdir -p ".local/bin" \
    && apt-get update -y \
    && apt-get install openjdk-17-jre-headless -y \
    && curl -s https://github.com/nextflow-io/nextflow/releases/download/v24.04.1/nextflow-24.04.1-all \
    && wget -qO- https://get.nextflow.io | bash \
    && chmod +x nextflow \
    && mv nextflow .local/bin \
    && python -m venv venv \
    && . venv/bin/activate \
    && pip install -r requirements.txt \
    && sed -i 's/\r$//g' ./dockerConf/start.sh \
    && chmod +x ./dockerConf/start.sh

ENV PATH="$PATH:/$WORKDIR/.local/bin"

ENTRYPOINT ["./dockerConf/start.sh"]
EXPOSE 8050
