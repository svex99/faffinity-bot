FROM docker.uclv.cu/python:3.8.5

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python", "src/bot.py"]
