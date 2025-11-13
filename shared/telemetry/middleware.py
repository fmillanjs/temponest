"""
FastAPI middleware for tracing and metrics.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add custom tracing attributes to requests.
    """

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.tracer = trace.get_tracer(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get current span (created by FastAPI instrumentor)
        span = trace.get_current_span()

        # Add custom attributes
        if span.is_recording():
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.method", request.method)

            # Add user/tenant info if available
            if hasattr(request.state, "user_id"):
                span.set_attribute("user.id", request.state.user_id)
            if hasattr(request.state, "tenant_id"):
                span.set_attribute("tenant.id", request.state.tenant_id)

        try:
            response = await call_next(request)

            # Add response attributes
            if span.is_recording():
                span.set_attribute("http.status_code", response.status_code)

                # Mark span as error if status >= 400
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))

            return response

        except Exception as e:
            # Record exception in span
            if span.is_recording():
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect custom metrics for requests.
    """

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

        # Get meter
        meter = metrics.get_meter(__name__)

        # Create metrics
        self.request_counter = meter.create_counter(
            name="http.server.requests",
            description="Total number of HTTP requests",
            unit="1",
        )

        self.request_duration = meter.create_histogram(
            name="http.server.duration",
            description="Duration of HTTP requests",
            unit="ms",
        )

        self.active_requests = meter.create_up_down_counter(
            name="http.server.active_requests",
            description="Number of active HTTP requests",
            unit="1",
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Common attributes
        attributes = {
            "http.method": request.method,
            "http.route": request.url.path,
            "service.name": self.service_name,
        }

        # Increment active requests
        self.active_requests.add(1, attributes)

        try:
            response = await call_next(request)

            # Add status code to attributes
            attributes["http.status_code"] = response.status_code

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            self.request_duration.record(duration_ms, attributes)
            self.request_counter.add(1, attributes)

            return response

        except Exception as e:
            # Record error metrics
            attributes["http.status_code"] = 500
            attributes["error.type"] = type(e).__name__

            duration_ms = (time.time() - start_time) * 1000
            self.request_duration.record(duration_ms, attributes)
            self.request_counter.add(1, attributes)

            raise

        finally:
            # Decrement active requests
            self.active_requests.add(-1, attributes)
