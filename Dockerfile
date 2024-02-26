FROM python:3.10


WORKDIR /blockchain/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get -y install nano micro
RUN apt-get -y install git
RUN apt-get -y install net-tools

COPY . .



