FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential libglib2.0-dev wpasupplicant && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir bluepy paho-mqtt python-dotenv requests

CMD ["python3", "ble_listener.py"]
