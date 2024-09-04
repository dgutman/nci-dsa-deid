FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED True

WORKDIR /app

# COPY requirements.txt /app

RUN pip install --upgrade pip
COPY /docs/app/requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update

RUN apt-get install libdmtx0b

COPY /docs/app /app/

#CMD python app.py
ENTRYPOINT ["python","app.py"]
