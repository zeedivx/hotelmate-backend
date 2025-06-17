FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Firebase credentials (if exists)
COPY firebase-admin-credentials.json* ./

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set Python path and run uvicorn
ENV PYTHONPATH=/app
WORKDIR /app
CMD ["python", "-c", "import sys; sys.path.insert(0, '/app'); from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"]
