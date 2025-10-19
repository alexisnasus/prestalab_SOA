FROM python:3.11-slim

WORKDIR /app

# Copiar archivos necesarios
COPY ./services/prart/requirements.txt /app/requirements.txt
COPY ./services/prart/app.py /app
COPY ./services/prart/models.py /app
COPY ./bus_client.py /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]