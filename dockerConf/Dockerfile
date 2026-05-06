FROM python:3.11

ARG WORKDIR
ARG UID
ARG GID
ARG DOCKER_GID

WORKDIR $WORKDIR

COPY . .
COPY --from=docker:20.10 /usr/local/bin/docker .local/bin/

ENV NXF_VER=24.04.1

RUN groupadd -g $GID appgroup \
    && useradd -u $UID -g $GID -m appuser \
    && groupadd -g $DOCKER_GID docker \
    && usermod -aG docker appuser \
    && mkdir -p ".local/bin" \
    && apt-get update -y \
    && apt-get install openjdk-21-jre-headless -y \
    && wget -qO- https://get.nextflow.io | bash \
    && chmod +x nextflow \
    && mv nextflow .local/bin \
    && python -m venv venv \
    && . venv/bin/activate \
    && pip install -r requirements.txt \
    && sed -i 's/\r$//g' ./dockerConf/start.sh \
    && chmod +x ./dockerConf/start.sh

ENV PATH="$PATH:/$WORKDIR/.local/bin"

USER appuser

EXPOSE 8050
