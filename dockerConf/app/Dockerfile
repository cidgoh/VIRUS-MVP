FROM continuumio/miniconda3

WORKDIR /app

COPY ./dockerConf/app/environment.yml .
COPY ./dockerConf/app/start.sh /start.sh

RUN apt-get update -y \
    && apt-get install default-jre -y \
    && wget -qO- https://get.nextflow.io | bash \
    && chmod +x nextflow \
    && mv /app/nextflow /usr/local/bin \
    && conda env create -f environment.yml \
    && sed -i 's/\r$//g' /start.sh \
    && chmod +x /start.sh

# https://pythonspeed.com/articles/activate-conda-dockerfile/
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "COVID-MVP", "/start.sh"]
EXPOSE 8050
