FROM python:3.11-slim

WORKDIR /app

# Copiar archivos necesarios
COPY ./services/gerep/app.py /app
COPY ./bus_client.py /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

RUN pip install fastapi uvicorn sqlalchemy pymysql reportlab httpx colorama sqlalchemy-utils

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]