FROM python:3.11-slim

WORKDIR /app

ENV API_PORT=8000
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/main.py .
COPY api/static ./static

EXPOSE ${API_PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${API_PORT}