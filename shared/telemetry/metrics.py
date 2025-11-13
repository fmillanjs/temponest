"""
Metrics collection using OpenTelemetry.
"""

import os
import logging
from typing import Optional
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT

logger = logging.getLogger(__name__)


def setup_metrics(
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    otlp_endpoint: Optional[str] = None,
    export_interval_millis: int = 60000,  # 60 seconds
    enable_console_export: bool = False,
) -> MeterProvider:
    """
    Set up OpenTelemetry metrics for a service.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        environment: Deployment environment
        otlp_endpoint: OTLP endpoint URL
        export_interval_millis: How often to export metrics (milliseconds)
        enable_console_export: If True, also export metrics to console

    Returns:
        MeterProvider instance
    """
    # Get OTLP endpoint from env if not provided
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    # Create resource
    resource = Resource.create({
        SERVICE_NAME: f"temponest-{service_name}",
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
        "service.namespace": "temponest",
    })

    # Create metric readers
    readers = []

    # Add OTLP metric exporter
    try:
        otlp_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        otlp_reader = PeriodicExportingMetricReader(
            otlp_exporter,
            export_interval_millis=export_interval_millis
        )
        readers.append(otlp_reader)
        logger.info(f"OTLP metric exporter configured: {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP metric exporter: {e}")

    # Add console exporter for debugging
    if enable_console_export:
        console_exporter = ConsoleMetricExporter()
        console_reader = PeriodicExportingMetricReader(
            console_exporter,
            export_interval_millis=export_interval_millis
        )
        readers.append(console_reader)
        logger.info("Console metric exporter enabled")

    # Create meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=readers
    )

    # Set global meter provider
    metrics.set_meter_provider(meter_provider)

    logger.info(f"Metrics initialized for service: {service_name}")
    return meter_provider


def get_meter(name: str, version: str = "1.0.0") -> metrics.Meter:
    """
    Get a meter for creating custom metrics.

    Args:
        name: Name of the meter (typically module name)
        version: Version of the meter

    Returns:
        Meter instance
    """
    return metrics.get_meter(name, version)
