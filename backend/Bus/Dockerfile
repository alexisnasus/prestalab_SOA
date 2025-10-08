FROM python:3.11-slim

WORKDIR /app

# Copiar requirements del proyecto principal
COPY ./requirements.txt .

# Actualizar e instalar curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir httpx

# Copiar el código del bus
COPY bus.py .

# Exponer el puerto del bus
EXPOSE 8000

# Comando para ejecutar el bus
CMD ["uvicorn", "bus:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
