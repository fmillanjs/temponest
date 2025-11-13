"""
Distributed tracing configuration using OpenTelemetry.
"""

import os
import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

logger = logging.getLogger(__name__)


def setup_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    otlp_endpoint: Optional[str] = None,
    enable_console_export: bool = False,
) -> TracerProvider:
    """
    Set up OpenTelemetry tracing for a service.

    Args:
        service_name: Name of the service (e.g., "agents", "auth")
        service_version: Version of the service
        environment: Deployment environment (development, staging, production)
        otlp_endpoint: OTLP endpoint URL (if None, uses env var OTEL_EXPORTER_OTLP_ENDPOINT)
        enable_console_export: If True, also export traces to console (useful for debugging)

    Returns:
        TracerProvider instance
    """
    # Get OTLP endpoint from env if not provided
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: f"temponest-{service_name}",
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
        "service.namespace": "temponest",
    })

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Add OTLP exporter (for Jaeger/Tempo)
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        logger.info(f"OTLP trace exporter configured: {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP exporter: {e}")

    # Add console exporter for debugging
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(console_exporter)
        tracer_provider.add_span_processor(console_processor)
        logger.info("Console trace exporter enabled")

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Auto-instrument common libraries
    _instrument_libraries()

    logger.info(f"Tracing initialized for service: {service_name}")
    return tracer_provider


def _instrument_libraries():
    """Auto-instrument common libraries for tracing."""
    try:
        # Instrument FastAPI
        FastAPIInstrumentor().instrument()
        logger.debug("FastAPI instrumentation enabled")
    except Exception as e:
        logger.debug(f"FastAPI instrumentation skipped: {e}")

    try:
        # Instrument AsyncPG (PostgreSQL)
        AsyncPGInstrumentor().instrument()
        logger.debug("AsyncPG instrumentation enabled")
    except Exception as e:
        logger.debug(f"AsyncPG instrumentation skipped: {e}")

    try:
        # Instrument Redis
        RedisInstrumentor().instrument()
        logger.debug("Redis instrumentation enabled")
    except Exception as e:
        logger.debug(f"Redis instrumentation skipped: {e}")

    try:
        # Instrument requests library
        RequestsInstrumentor().instrument()
        logger.debug("Requests instrumentation enabled")
    except Exception as e:
        logger.debug(f"Requests instrumentation skipped: {e}")

    try:
        # Instrument httpx
        HTTPXClientInstrumentor().instrument()
        logger.debug("HTTPX instrumentation enabled")
    except Exception as e:
        logger.debug(f"HTTPX instrumentation skipped: {e}")


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer for creating custom spans.

    Args:
        name: Name of the tracer (typically module name)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
