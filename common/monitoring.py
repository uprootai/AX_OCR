"""
Prometheus Monitoring Metrics

시스템 메트릭 수집 및 노출
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Optional
import time

# =============================================================================
# Metrics Definitions
# =============================================================================

# Request counters
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Response time histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Active requests gauge
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# OCR processing metrics
ocr_processing_total = Counter(
    'ocr_processing_total',
    'Total OCR processing requests',
    ['strategy', 'status']
)

ocr_processing_duration_seconds = Histogram(
    'ocr_processing_duration_seconds',
    'OCR processing duration in seconds',
    ['strategy']
)

ocr_dimensions_extracted = Counter(
    'ocr_dimensions_extracted_total',
    'Total number of dimensions extracted',
    ['strategy']
)

ocr_gdt_extracted = Counter(
    'ocr_gdt_extracted_total',
    'Total number of GD&T symbols extracted',
    ['strategy']
)

# EDGNet metrics
edgnet_components_detected = Counter(
    'edgnet_components_detected_total',
    'Total number of components detected by EDGNet'
)

edgnet_processing_duration_seconds = Histogram(
    'edgnet_processing_duration_seconds',
    'EDGNet processing duration in seconds'
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['service']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service']
)

# Service info
service_info = Info(
    'service',
    'Service information'
)

# Error counter
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['service', 'error_type']
)


# =============================================================================
# Helper Functions
# =============================================================================

def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_ocr_processing(
    strategy: str,
    status: str,
    duration: float,
    dimensions_count: int = 0,
    gdt_count: int = 0
):
    """Record OCR processing metrics"""
    ocr_processing_total.labels(strategy=strategy, status=status).inc()
    ocr_processing_duration_seconds.labels(strategy=strategy).observe(duration)

    if dimensions_count > 0:
        ocr_dimensions_extracted.labels(strategy=strategy).inc(dimensions_count)

    if gdt_count > 0:
        ocr_gdt_extracted.labels(strategy=strategy).inc(gdt_count)


def record_edgnet_processing(components_count: int, duration: float):
    """Record EDGNet processing metrics"""
    edgnet_components_detected.inc(components_count)
    edgnet_processing_duration_seconds.observe(duration)


def record_circuit_breaker_state(service: str, state: str):
    """Record circuit breaker state"""
    state_value = {"closed": 0, "half_open": 1, "open": 2}.get(state, 0)
    circuit_breaker_state.labels(service=service).set(state_value)


def record_error(service: str, error_type: str):
    """Record an error"""
    errors_total.labels(service=service, error_type=error_type).inc()


# =============================================================================
# FastAPI Integration
# =============================================================================

async def metrics_endpoint():
    """
    Prometheus metrics endpoint

    Usage in FastAPI:
        @app.get("/metrics")
        async def metrics():
            return await metrics_endpoint()
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class PrometheusMiddleware:
    """
    FastAPI middleware to automatically track HTTP metrics

    Usage:
        from fastapi import FastAPI
        from common.monitoring import PrometheusMiddleware

        app = FastAPI()
        app.add_middleware(PrometheusMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # Skip metrics endpoint itself
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()
        start_time = time.time()

        # Process request
        status_code = 200
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            http_requests_in_progress.labels(method=method, endpoint=path).dec()
            record_request(method, path, status_code, duration)


# Initialize service info
service_info.info({
    'name': 'AX Drawing Analysis System',
    'version': '2.0.0'
})
