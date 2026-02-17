FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY . .

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV API_PORT=8000

# Run the API
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
