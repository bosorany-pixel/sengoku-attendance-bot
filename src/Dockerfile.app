FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y iproute2 && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY ./src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src .
RUN mkdir -p /db
CMD ["python", "app.py"]