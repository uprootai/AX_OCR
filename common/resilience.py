"""
Resilience Patterns: Retry and Circuit Breaker

서비스 간 통신의 안정성을 높이는 패턴들
"""

import asyncio
import time
from typing import Callable, Any, Optional
from functools import wraps
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Retry Logic with Exponential Backoff
# =============================================================================

async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 10.0)
        exponential_base: Backoff multiplier (default: 2.0)
        exceptions: Tuple of exceptions to catch (default: all exceptions)

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail

    Example:
        result = await retry_async(
            lambda: http_client.post(...),
            max_attempts=3
        )
    """
    attempt = 0
    last_exception = None

    while attempt < max_attempts:
        try:
            result = await func()
            if attempt > 0:
                logger.info(f"✅ Retry succeeded on attempt {attempt + 1}")
            return result

        except exceptions as e:
            attempt += 1
            last_exception = e

            if attempt >= max_attempts:
                logger.error(f"❌ All {max_attempts} retry attempts failed")
                raise

            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** (attempt - 1)), max_delay)

            logger.warning(
                f"⚠️  Attempt {attempt}/{max_attempts} failed: {str(e)[:100]}. "
                f"Retrying in {delay:.1f}s..."
            )

            await asyncio.sleep(delay)

    raise last_exception


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to add retry logic to async functions

    Example:
        @with_retry(max_attempts=3)
        async def call_external_api():
            response = await http_client.get("https://api.example.com")
            return response.json()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                exceptions=exceptions
            )
        return wrapper
    return decorator


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation

    Prevents cascading failures by stopping requests to a failing service.

    States:
        - CLOSED: Normal operation
        - OPEN: Too many failures, reject all requests
        - HALF_OPEN: Allow one request to test recovery

    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60.0
        )

        async with breaker:
            response = await http_client.get("https://external-api.com")
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        name: str = "default"
    ):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds to wait before trying half-open state
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

    def _should_attempt(self) -> bool:
        """Check if request should be attempted"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                logger.info(f"🔄 Circuit '{self.name}' transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allow one request
        return True

    def _record_success(self):
        """Record a successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info(f"✅ Circuit '{self.name}' CLOSED (service recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0

    def _record_failure(self):
        """Record a failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"⚠️  Circuit '{self.name}' reopening (half-open test failed)")
            self.state = CircuitState.OPEN
            self.success_count = 0

        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"❌ Circuit '{self.name}' OPEN "
                f"({self.failure_count} failures, threshold: {self.failure_threshold})"
            )
            self.state = CircuitState.OPEN

    async def call(self, func: Callable) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Async function to execute

        Returns:
            Result of the function call

        Raises:
            RuntimeError: If circuit is open
            Any exception from the function
        """
        if not self._should_attempt():
            raise RuntimeError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable (last failure: {time.time() - self.last_failure_time:.0f}s ago)"
            )

        try:
            result = await func()
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    async def __aenter__(self):
        """Context manager entry"""
        if not self._should_attempt():
            raise RuntimeError(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            self._record_success()
        else:
            self._record_failure()
        return False

    @property
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == CircuitState.OPEN

    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "is_open": self.is_open
        }


# =============================================================================
# Global Circuit Breakers for Services
# =============================================================================

# Create circuit breakers for each external service
CIRCUIT_BREAKERS = {
    "edocr2-v1": CircuitBreaker(failure_threshold=5, timeout=60, name="eDOCr2-v1"),
    "edocr2-v2": CircuitBreaker(failure_threshold=5, timeout=60, name="eDOCr2-v2"),
    "edgnet": CircuitBreaker(failure_threshold=5, timeout=60, name="EDGNet"),
    "skinmodel": CircuitBreaker(failure_threshold=5, timeout=60, name="SkinModel"),
}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get circuit breaker for a service"""
    return CIRCUIT_BREAKERS.get(
        service_name,
        CircuitBreaker(name=service_name)
    )
