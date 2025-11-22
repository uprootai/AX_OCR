"""
Advanced Logging Configuration
파일 기반 구조화된 로깅 시스템

Features:
- JSON formatted logging for easy parsing
- Separate error log file
- Request ID tracking for distributed tracing
- Contextual information (module, function, line number)
- Performance metrics logging
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback
from contextvars import ContextVar

# Context variable for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    JSON 포맷 로거
    구조화된 로그를 JSON 형식으로 출력하여 파싱 및 분석 용이
    """

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 변환"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add custom fields from extra
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class ContextAdapter(logging.LoggerAdapter):
    """
    컨텍스트 정보를 추가하는 로거 어댑터
    추가 정보를 로그에 포함시킬 수 있음
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """메시지 처리 시 extra 필드 추가"""
        extra = kwargs.get("extra", {})

        # Add request_id if available
        request_id = request_id_var.get()
        if request_id:
            extra["request_id"] = request_id

        kwargs["extra"] = {"extra_fields": extra}
        return msg, kwargs


def setup_logging(
    app_name: str = "gateway-api",
    log_dir: str = "/tmp/gateway/logs",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_json: bool = True
) -> logging.Logger:
    """
    로깅 시스템 초기화

    Args:
        app_name: 애플리케이션 이름 (로그 파일명에 사용)
        log_dir: 로그 파일 저장 디렉토리
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: 콘솔 출력 활성화 여부
        enable_json: JSON 포맷 사용 여부

    Returns:
        설정된 로거 인스턴스
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()  # Clear existing handlers

    # File paths
    general_log_file = log_path / f"{app_name}.log"
    error_log_file = log_path / f"{app_name}_error.log"

    # Formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
        )

    # General log file handler (all levels)
    general_handler = logging.handlers.RotatingFileHandler(
        general_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    general_handler.setLevel(logging.DEBUG)
    general_handler.setFormatter(formatter)
    logger.addHandler(general_handler)

    # Error log file handler (ERROR and above only)
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Console handler (if enabled)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Use simple format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info(f"Logging initialized: {app_name}")
    logger.info(f"Log directory: {log_dir}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"General log: {general_log_file}")
    logger.info(f"Error log: {error_log_file}")

    return logger


def get_logger(name: str) -> ContextAdapter:
    """
    컨텍스트 정보를 지원하는 로거 반환

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)

    Returns:
        ContextAdapter 인스턴스

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", extra={"user_id": 123, "action": "upload"})
    """
    return ContextAdapter(logging.getLogger(name), {})


def set_request_id(request_id: str):
    """
    현재 요청의 ID 설정 (분산 추적용)

    Args:
        request_id: 요청 ID (UUID 등)
    """
    request_id_var.set(request_id)


def clear_request_id():
    """현재 요청 ID 초기화"""
    request_id_var.set(None)


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """
    성능 메트릭 로깅

    Args:
        logger: 로거 인스턴스
        operation: 작업 이름
        duration: 작업 소요 시간 (초)
        **kwargs: 추가 컨텍스트 정보
    """
    extra = {
        "metric_type": "performance",
        "operation": operation,
        "duration_seconds": round(duration, 4),
        **kwargs
    }
    logger.info(f"Performance: {operation} completed in {duration:.4f}s", extra=extra)


def log_api_call(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: int,
    duration: float,
    **kwargs
):
    """
    API 호출 로깅

    Args:
        logger: 로거 인스턴스
        method: HTTP 메서드
        url: API URL
        status_code: HTTP 상태 코드
        duration: 요청 소요 시간 (초)
        **kwargs: 추가 정보 (request_id, user_id 등)
    """
    extra = {
        "metric_type": "api_call",
        "http_method": method,
        "url": url,
        "status_code": status_code,
        "duration_seconds": round(duration, 4),
        **kwargs
    }

    level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
    logger.log(
        level,
        f"API Call: {method} {url} - {status_code} ({duration:.4f}s)",
        extra=extra
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    notify: bool = True
):
    """
    에러 상세 로깅

    Args:
        logger: 로거 인스턴스
        error: 예외 객체
        context: 추가 컨텍스트 정보
        notify: 알림 전송 여부 (향후 이메일/슬랙 연동용)
    """
    extra = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "notify": notify,
        **(context or {})
    }

    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra=extra
    )


# Export commonly used functions
__all__ = [
    'setup_logging',
    'get_logger',
    'set_request_id',
    'clear_request_id',
    'log_performance',
    'log_api_call',
    'log_error',
    'JSONFormatter',
    'ContextAdapter'
]
