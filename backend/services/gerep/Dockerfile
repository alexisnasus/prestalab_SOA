FROM python:3.11-slim

WORKDIR /app

# Dependencias
COPY ./services/gerep/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Código del servicio
COPY ./services/gerep/app.py    /app/app.py
COPY ./services/gerep/models.py /app/models.py

# Utilitarios compartidos (están dentro de ./Bus/)
COPY ./bus_client.py     /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
