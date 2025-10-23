FROM python:3.11-slim

WORKDIR /app

COPY ./services/sugit/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./services/sugit/app.py    /app/app.py
COPY ./services/sugit/models.py /app/models.py

CMD ["python", "app.py"]
