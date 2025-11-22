"""
FastAPI Logging Middleware
모든 API 요청/응답을 자동으로 로깅하는 미들웨어

Features:
- Automatic request/response logging
- Request ID generation and tracking
- Performance monitoring
- Error tracking with full context
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utils.logger import (
    get_logger,
    set_request_id,
    clear_request_id,
    log_api_call,
    log_error
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    API 요청/응답 로깅 미들웨어

    - 모든 요청에 고유 request_id 할당
    - 요청 시작/완료 로깅
    - 성능 메트릭 수집
    - 에러 자동 캡처 및 로깅
    """

    def __init__(self, app: ASGIApp, log_request_body: bool = False, log_response_body: bool = False):
        """
        Args:
            app: FastAPI 애플리케이션
            log_request_body: 요청 본문 로깅 여부 (주의: 민감정보 포함 가능)
            log_response_body: 응답 본문 로깅 여부 (주의: 큰 응답의 경우 성능 영향)
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """요청 처리 및 로깅"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Extract request info
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Start timing
        start_time = time.time()

        # Log request start
        logger.info(
            f"Request started: {method} {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "client_host": client_host,
                "user_agent": user_agent,
                "event": "request_start"
            }
        )

        # Log request body if enabled (for debugging)
        if self.log_request_body and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) < 10000:  # Only log if < 10KB
                    logger.debug(
                        f"Request body: {body[:1000]}...",
                        extra={
                            "request_id": request_id,
                            "body_size": len(body)
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to log request body: {e}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code

            # Log API call
            log_api_call(
                logger,
                method=method,
                url=url,
                status_code=status_code,
                duration=duration,
                request_id=request_id,
                client_host=client_host
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error with full context
            log_error(
                logger,
                error=e,
                context={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "client_host": client_host,
                    "duration_seconds": duration
                },
                notify=True
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )

        finally:
            # Clean up request context
            clear_request_id()


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    성능 모니터링 미들웨어
    느린 요청을 자동으로 감지하고 경고
    """

    def __init__(self, app: ASGIApp, slow_request_threshold: float = 5.0):
        """
        Args:
            app: FastAPI 애플리케이션
            slow_request_threshold: 느린 요청 임계값 (초)
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """요청 처리 시간 모니터링"""
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Warn about slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} took {duration:.2f}s",
                extra={
                    "metric_type": "slow_request",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_seconds": duration,
                    "threshold": self.slow_request_threshold
                }
            )

        return response


def setup_logging_middleware(app, log_request_body: bool = False, slow_request_threshold: float = 5.0):
    """
    FastAPI 앱에 로깅 미들웨어 추가

    Args:
        app: FastAPI 애플리케이션
        log_request_body: 요청 본문 로깅 여부
        slow_request_threshold: 느린 요청 임계값 (초)

    Example:
        from fastapi import FastAPI
        from utils.logging_middleware import setup_logging_middleware

        app = FastAPI()
        setup_logging_middleware(app, slow_request_threshold=3.0)
    """
    # Add performance monitoring middleware first (outer layer)
    app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold=slow_request_threshold)

    # Add logging middleware (inner layer)
    app.add_middleware(LoggingMiddleware, log_request_body=log_request_body)

    logger.info("Logging middleware configured")
    logger.info(f"Request body logging: {'enabled' if log_request_body else 'disabled'}")
    logger.info(f"Slow request threshold: {slow_request_threshold}s")


__all__ = [
    'LoggingMiddleware',
    'PerformanceLoggingMiddleware',
    'setup_logging_middleware'
]
