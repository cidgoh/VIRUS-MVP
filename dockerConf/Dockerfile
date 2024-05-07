FROM continuumio/miniconda3

WORKDIR /app

COPY . .

RUN mkdir "cache_directory" \
    mkdir -p ".local/bin" \
    && apt-get update -y \
    && apt-get install default-jre -y \
    && wget -qO- https://get.nextflow.io | bash \
    && chmod +x nextflow \
    && mv nextflow .local/bin \
    && conda env create -f ./dockerConf/environment.yml \
    && sed -i 's/\r$//g' ./dockerConf/start.sh \
    && chmod +x ./dockerConf/start.sh

ENV PATH="${PATH}:/app/.local/bin"

# https://pythonspeed.com/articles/activate-conda-dockerfile/
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "VIRUS-MVP", "./dockerConf/start.sh"]
EXPOSE 8050
