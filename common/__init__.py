"""
Common utilities for AX Drawing Analysis System

Provides:
- Authentication (auth.py)
- Rate limiting (rate_limiter.py)
- Retry and Circuit Breaker (resilience.py)
- Monitoring (monitoring.py)
"""

from .auth import verify_api_key, require_auth, AUTHENTICATION_ENABLED
from .rate_limiter import check_rate_limit, rate_limiter, RATE_LIMIT_ENABLED
from .resilience import (
    retry_async,
    with_retry,
    CircuitBreaker,
    CircuitState,
    get_circuit_breaker,
    CIRCUIT_BREAKERS
)
from .monitoring import (
    metrics_endpoint,
    PrometheusMiddleware,
    record_request,
    record_ocr_processing,
    record_edgnet_processing,
    record_circuit_breaker_state,
    record_error
)

__all__ = [
    # Auth
    'verify_api_key',
    'require_auth',
    'AUTHENTICATION_ENABLED',
    
    # Rate limiting
    'check_rate_limit',
    'rate_limiter',
    'RATE_LIMIT_ENABLED',
    
    # Resilience
    'retry_async',
    'with_retry',
    'CircuitBreaker',
    'CircuitState',
    'get_circuit_breaker',
    'CIRCUIT_BREAKERS',
    
    # Monitoring
    'metrics_endpoint',
    'PrometheusMiddleware',
    'record_request',
    'record_ocr_processing',
    'record_edgnet_processing',
    'record_circuit_breaker_state',
    'record_error',
]
