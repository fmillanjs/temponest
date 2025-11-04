FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy SDK first and install
COPY sdk /tmp/sdk
RUN pip install --no-cache-dir /tmp/sdk && rm -rf /tmp/sdk

# Copy requirements and install
COPY web-ui/requirements.txt .
RUN pip install --no-cache-dir Flask>=3.0.0 python-dotenv>=1.0.0 requests>=2.31.0 PyYAML>=6.0 asyncpg>=0.30.0

# Copy application
COPY web-ui/ .

# Copy config directory for department YAML files
COPY config /config

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
