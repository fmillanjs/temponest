# Stage 1: Builder - Install dependencies
# NOTE: Using Debian (slim) instead of Alpine because:
# - onnxruntime (required by chromadb) doesn't provide musllinux wheels
# - Building from source is too slow and unreliable
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to a virtual environment
COPY services/agents/requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    PIP_DEFAULT_TIMEOUT=300 pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (preserve directory structure)
COPY services/agents/app/ /app/app/

# Copy shared modules
COPY shared/ /app/shared/

# Create output directory
RUN mkdir -p /output

# Add shared modules to PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Run the application (now that app/ is a proper module)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
