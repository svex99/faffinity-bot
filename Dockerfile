FROM docker.uclv.cu/python:3.9.5

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt
