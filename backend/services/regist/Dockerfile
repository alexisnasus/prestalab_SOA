FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libffi-dev pkg-config gcc \
 && rm -rf /var/lib/apt/lists/*

COPY ./services/regist/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    (pip install --no-cache-dir -r requirements.txt || \
     (sleep 5 && pip install --no-cache-dir -r requirements.txt))

COPY ./services/regist/app.py    /app/app.py
COPY ./services/regist/models.py /app/models.py

COPY ./bus_client.py     /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
