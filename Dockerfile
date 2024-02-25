FROM python:3.10


WORKDIR /blockchain/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get -y install nano micro
RUN apt-get -y install git

COPY . .

CMD ["python3","server.py"]

