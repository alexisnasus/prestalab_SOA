FROM python:3.11-slim

WORKDIR /app

# Copiar archivos necesarios
COPY ./services/gerep/requirements.txt /app/requirements.txt
COPY ./services/gerep/app.py /app
COPY ./services/gerep/models.py /app
COPY ./bus_client.py /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]