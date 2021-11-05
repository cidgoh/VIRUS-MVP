FROM continuumio/anaconda3

RUN apt-get update -y\
  && apt-get install git -y

WORKDIR /app

# Make RUN commands use `bash --login`:
SHELL ["/bin/bash", "--login", "-c"]

## create conda env
COPY ./dockerConf/app/condaEnviroment.yml .
RUN conda env create -f condaEnviroment.yml
RUN conda init bash

# Activate the environment
RUN conda activate covidMVP

# Requirements are installed here to ensure they will be cached.
COPY requirements.txt .
RUN pip install -r /app/requirements.txt \
    && rm -rf /app/requirements.txt


COPY . /app

COPY ./dockerConf/app/start.sh /start.sh
RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]

EXPOSE 8050
