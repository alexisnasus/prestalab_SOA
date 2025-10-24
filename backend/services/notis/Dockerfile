FROM python:3.11-slim

WORKDIR /app

COPY ./services/notis/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./services/notis/app.py    /app/app.py
COPY ./services/notis/models.py /app/models.py

CMD ["python", "app.py"]
