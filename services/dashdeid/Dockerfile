FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED True

WORKDIR /app

# COPY requirements.txt /app

RUN pip install --upgrade pip

# Install build dependencies for psutil and other packages that need compilation
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libdmtx0b \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

#CMD python app.py
ENTRYPOINT ["python","app.py"]
