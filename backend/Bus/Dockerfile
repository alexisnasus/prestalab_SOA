# backend/Bus/Dockerfile
FROM python:3.11-slim

# curl para el healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias: el requirements.txt está en backend/bus/
COPY bus/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copiar TODO el código del servicio (backend/Bus/*) a /app
COPY Bus/ /app/
WORKDIR /app

EXPOSE 8000

# Arrancar la app:
# 1) Si en Bus/bus.py defines `app = FastAPI()`:
CMD ["uvicorn", "bus:app", "--host", "0.0.0.0", "--port", "8000"]

# 2) Si prefieres ejecutar un script (y éste arranca el servidor):
# CMD ["python", "bus.py"]
