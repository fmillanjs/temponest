# OpenTelemetry Integration Guide

This guide explains how to integrate OpenTelemetry tracing and metrics into TempoNest services.

## Overview

OpenTelemetry provides:
- **Distributed Tracing**: Track requests across services
- **Metrics Collection**: Monitor performance and resource usage
- **Automatic Instrumentation**: Auto-instrument FastAPI, PostgreSQL, Redis, etc.

## Quick Start

### 1. Install Dependencies

Add to your service's `requirements.txt`:

```bash
# Include shared telemetry requirements
-r ../../shared/requirements-telemetry.txt
```

Or manually add:
```
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-exporter-otlp-proto-grpc>=1.20.0
opentelemetry-instrumentation-fastapi>=0.41b0
opentelemetry-instrumentation-asyncpg>=0.41b0
opentelemetry-instrumentation-redis>=0.41b0
```

### 2. Initialize Telemetry in Your Service

Add to your `main.py` (before creating FastAPI app):

```python
import os
import logging

# Import shared telemetry module
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from shared.telemetry import (
        setup_tracing,
        setup_metrics,
        TracingMiddleware,
        MetricsMiddleware,
    )
    TELEMETRY_ENABLED = True
except ImportError:
    TELEMETRY_ENABLED = False
    logging.warning("OpenTelemetry not available - telemetry disabled")

# Initialize telemetry (during startup)
if TELEMETRY_ENABLED:
    environment = os.getenv("ENVIRONMENT", "development")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")

    # Setup tracing
    setup_tracing(
        service_name="agents",  # Change to your service name
        service_version="1.0.0",
        environment=environment,
        otlp_endpoint=otlp_endpoint,
        enable_console_export=(environment == "development"),
    )

    # Setup metrics
    setup_metrics(
        service_name="agents",  # Change to your service name
        service_version="1.0.0",
        environment=environment,
        otlp_endpoint=otlp_endpoint,
        export_interval_millis=60000,  # Export every 60 seconds
    )
```

### 3. Add Middleware to FastAPI App

```python
# Create FastAPI app
app = FastAPI(title="Your Service", lifespan=lifespan)

# Add telemetry middleware
if TELEMETRY_ENABLED:
    app.add_middleware(TracingMiddleware, service_name="agents")
    app.add_middleware(MetricsMiddleware, service_name="agents")

# Add other middleware (CORS, etc.)
app.add_middleware(CORSMiddleware, ...)
```

### 4. Update Dockerfile

Ensure the shared module is available in your Dockerfile:

```dockerfile
# In your service's Dockerfile
ENV PYTHONPATH=/app:/app/shared

# Copy shared modules
COPY shared/ /app/shared/
```

### 5. Update Docker Compose

Add environment variables to your service in `docker-compose.yml`:

```yaml
services:
  agents:
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - ENVIRONMENT=production
```

## Start Observability Stack

### Option 1: Jaeger (Recommended for Development)

```bash
# Start all services with Jaeger
docker compose -f docker/docker-compose.yml -f docker/docker-compose.telemetry.yml up -d
```

Access Jaeger UI: http://localhost:16686

### Option 2: Tempo + Grafana (Recommended for Production)

Tempo is already included in the telemetry stack. Access:
- Grafana: http://localhost:3001 (view traces)
- Tempo API: http://localhost:3200

## Custom Tracing

### Add Custom Spans

```python
from shared.telemetry import get_tracer

tracer = get_tracer(__name__)

@app.get("/api/custom")
async def custom_endpoint():
    with tracer.start_as_current_span("custom-operation") as span:
        span.set_attribute("custom.attribute", "value")

        # Your code here
        result = await do_something()

        span.set_attribute("result.count", len(result))
        return result
```

### Add Custom Metrics

```python
from shared.telemetry import get_meter

meter = get_meter(__name__)

# Create a counter
request_counter = meter.create_counter(
    name="custom.requests",
    description="Number of custom requests",
    unit="1",
)

# Use the counter
request_counter.add(1, {"status": "success"})
```

## Automatic Instrumentation

The following libraries are automatically instrumented:

- ✅ **FastAPI**: All HTTP requests/responses
- ✅ **AsyncPG**: Database queries
- ✅ **Redis**: Cache operations
- ✅ **Requests**: HTTP client calls
- ✅ **HTTPX**: Async HTTP client calls

No additional code required!

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |
| `OTEL_SERVICE_NAME` | Service name | Set programmatically |
| `ENVIRONMENT` | Deployment environment | `development` |

## Trace Context Propagation

Traces automatically propagate across services when using:
- HTTP calls (via requests/httpx)
- FastAPI endpoints
- Database queries

Example - Service-to-Service call:
```python
import httpx

# Trace context is automatically propagated
async with httpx.AsyncClient() as client:
    response = await client.get("http://auth-service/api/v1/users")
```

## Viewing Traces

### Jaeger UI

1. Open http://localhost:16686
2. Select service: `temponest-agents`, `temponest-auth`, etc.
3. Click "Find Traces"
4. View detailed span information

### Grafana + Tempo

1. Open http://localhost:3001
2. Go to Explore
3. Select "Tempo" data source
4. Search by:
   - Service name
   - Operation name
   - Tags (e.g., `http.status_code=500`)

## Performance Impact

- **Tracing overhead**: < 1% CPU, < 10MB memory
- **Metrics overhead**: < 0.5% CPU, < 5MB memory
- **Network**: Batched exports every 60s

## Troubleshooting

### Traces Not Appearing

1. Check if Jaeger/Tempo is running:
   ```bash
   docker ps | grep jaeger
   ```

2. Check service logs for telemetry errors:
   ```bash
   docker logs temponest-agents | grep -i "telemetry\|otel"
   ```

3. Verify OTLP endpoint:
   ```bash
   curl http://localhost:4317 -v
   ```

### High Memory Usage

Reduce export frequency:
```python
setup_metrics(
    export_interval_millis=120000,  # Export every 2 minutes
)
```

### Disable Telemetry

Set environment variable or remove imports:
```bash
# In docker-compose.yml
environment:
  - TELEMETRY_ENABLED=false
```

## Production Recommendations

1. **Use Tempo** instead of Jaeger (lower resource usage)
2. **Sample traces** in high-traffic environments:
   ```python
   from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

   # Sample 10% of traces
   sampler = TraceIdRatioBased(0.1)
   ```

3. **Export to external backends**:
   - Grafana Cloud
   - Honeycomb
   - New Relic
   - Datadog

4. **Monitor telemetry resource usage**:
   ```bash
   docker stats temponest-jaeger
   ```

## Reference

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [Jaeger Docs](https://www.jaegertracing.io/docs/)
- [Grafana Tempo Docs](https://grafana.com/docs/tempo/latest/)
