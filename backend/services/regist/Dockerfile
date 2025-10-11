FROM python:3.11-slim

WORKDIR /app

# Copiar archivos necesarios
COPY ./services/regist/app.py /app
COPY ./bus_client.py /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

# Instalar dependencias del sistema necesarias para cryptography
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y luego instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install fastapi uvicorn sqlalchemy pymysql cryptography httpx colorama email-validator

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
