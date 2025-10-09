FROM python:3.11-slim

WORKDIR /app

# Copiar archivos necesarios
COPY app.py /app
COPY ../../bus_client.py /app/bus_client.py

RUN pip install fastapi uvicorn sqlalchemy pymysql reportlab httpx

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]