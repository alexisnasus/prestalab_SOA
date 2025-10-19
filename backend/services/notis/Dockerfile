FROM python:3.11-slim

WORKDIR /app

# Copiar archivos necesarios
COPY ./services/notis/requirements.txt /app/requirements.txt
COPY ./services/notis/app.py /app
COPY ./services/notis/models.py /app
COPY ./bus_client.py /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]