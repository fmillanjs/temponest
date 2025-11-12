# Stage 1: Builder - Install dependencies
FROM python:3.10-alpine AS builder

WORKDIR /app

# Install build dependencies for Alpine
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

# Copy SDK first and install to virtual environment
COPY sdk /tmp/sdk
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /tmp/sdk && \
    rm -rf /tmp/sdk

# Install application dependencies
RUN pip install --no-cache-dir Flask>=3.0.0 python-dotenv>=1.0.0 requests>=2.31.0 PyYAML>=6.0 asyncpg>=0.30.0

# Stage 2: Runtime - Minimal production image
FROM python:3.10-alpine AS runtime

WORKDIR /app

# Install only runtime dependencies
RUN apk add --no-cache \
    curl \
    libpq

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY web-ui/ .

# Copy config directory for department YAML files
COPY config /config

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
