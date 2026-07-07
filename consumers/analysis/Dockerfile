FROM python:3.11-slim

WORKDIR /app

COPY consumers/analysis/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY consumers/analysis/main.py /app/main.py

CMD ["python", "main.py"]