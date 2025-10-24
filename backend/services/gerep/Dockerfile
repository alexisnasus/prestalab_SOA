FROM python:3.11-slim

WORKDIR /app

# Dependencias
COPY ./services/gerep/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Código del servicio
COPY ./services/gerep/app.py    /app/app.py
COPY ./services/gerep/models.py /app/models.py

CMD ["python", "app.py"]
