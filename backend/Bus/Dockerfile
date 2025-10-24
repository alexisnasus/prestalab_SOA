FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY bus.py /app/bus.py

# Persistencia del bus (mapeada por volumen desde docker-compose)
RUN mkdir -p /app/bus_data

EXPOSE 5000
CMD ["uvicorn", "bus:app", "--host", "0.0.0.0", "--port", "5000"]
