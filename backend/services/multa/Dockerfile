FROM python:3.11-slim

WORKDIR /app

COPY ./services/multa/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./services/multa/app.py    /app/app.py
COPY ./services/multa/models.py /app/models.py

COPY ./bus_client.py     /app/bus_client.py
COPY ./service_logger.py /app/service_logger.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
