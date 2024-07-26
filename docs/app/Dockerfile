FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=True

WORKDIR /app

COPY requirements.txt /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update

RUN apt-get install libdmtx0b

COPY start.sh /app

RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]
