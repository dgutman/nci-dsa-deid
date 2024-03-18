FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY requirements.txt /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# CMD python app.py
CMD bash