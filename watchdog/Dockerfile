FROM python:3.11-slim

WORKDIR /app

# Instala o cliente Docker dentro do container
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

COPY watchdog.py .

CMD ["python3", "watchdog.py"]
