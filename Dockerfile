FROM docker.uclv.cu/python:3.8.5

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt \
    --index-url http://nexus.prod.uci.cu/repository/pypi-proxy/simple/ \
    --trusted-host nexus.prod.uci.cu

