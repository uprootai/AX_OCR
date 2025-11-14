"""
Advanced Features for Gateway API
- Request caching
- Retry logic with exponential backoff
- Timeout management
- Circuit breaker pattern
"""

import asyncio
import hashlib
import json
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# =====================
# Cache System
# =====================

class SimpleCache:
    """간단한 인메모리 캐시"""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl  # Time to live in seconds
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """캐시 항목이 만료되었는지 확인"""
        return time.time() > entry['expires_at']
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry):
                logger.info(f"✅ Cache hit: {key[:50]}...")
                return entry['data']
            else:
                # 만료된 항목 제거
                del self.cache[key]
                logger.info(f"⏰ Cache expired: {key[:50]}...")
        return None
    
    def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        self.cache[key] = {
            'data': value,
            'expires_at': time.time() + self.ttl,
            'created_at': time.time()
        }
        logger.info(f"💾 Cached: {key[:50]}...")
    
    def clear(self):
        """전체 캐시 클리어"""
        self.cache.clear()
        logger.info("🗑️  Cache cleared")
    
    def cleanup_expired(self):
        """만료된 캐시 항목 정리"""
        expired_keys = [k for k, v in self.cache.items() if self._is_expired(v)]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.info(f"🗑️  Cleaned up {len(expired_keys)} expired cache entries")

# Global cache instance
response_cache = SimpleCache(ttl=1800)  # 30분 TTL

def generate_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    """캐시 키 생성 (엔드포인트 + 파라미터 해시)"""
    params_str = json.dumps(params, sort_keys=True)
    hash_value = hashlib.md5(params_str.encode()).hexdigest()
    return f"{endpoint}:{hash_value}"

# =====================
# Retry Logic with Exponential Backoff
# =====================

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    지수 백오프를 사용한 재시도 로직
    
    Args:
        func: 재시도할 비동기 함수
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 대기 시간 (초)
        max_delay: 최대 대기 시간 (초)
        backoff_factor: 백오프 계수
        exceptions: 재시도할 예외 튜플
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            result = await func()
            if attempt > 0:
                logger.info(f"✅ Retry succeeded on attempt {attempt + 1}")
            return result
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = min(delay, max_delay)
                logger.warning(
                    f"⚠️  Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)[:100]}"
                    f"\n   Retrying in {wait_time:.1f}s..."
                )
                await asyncio.sleep(wait_time)
                delay *= backoff_factor
            else:
                logger.error(f"❌ All {max_retries + 1} attempts failed")
    
    raise last_exception

# =====================
# Timeout Management
# =====================

async def with_timeout(coro, timeout: float, timeout_message: str = "Operation timed out"):
    """
    타임아웃이 있는 비동기 작업 실행
    
    Args:
        coro: 코루틴
        timeout: 타임아웃 시간 (초)
        timeout_message: 타임아웃 메시지
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"⏱️  Timeout after {timeout}s: {timeout_message}")
        raise TimeoutError(f"{timeout_message} (timeout: {timeout}s)")

# =====================
# Circuit Breaker Pattern
# =====================

class CircuitBreaker:
    """
    서킷 브레이커 패턴 구현
    연속된 실패가 threshold를 넘으면 일정 시간 동안 요청을 차단
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    def _should_attempt_reset(self) -> bool:
        """복구 시도를 해야 하는지 확인"""
        return (
            self.state == "open" and
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    async def call(self, func: Callable):
        """서킷 브레이커를 통해 함수 호출"""
        
        # Open 상태 - 복구 시도 확인
        if self._should_attempt_reset():
            logger.info("🔄 Circuit breaker: Attempting recovery (half-open)")
            self.state = "half_open"
        
        # Open 상태 - 즉시 실패
        if self.state == "open":
            raise Exception(
                f"Circuit breaker is OPEN. Service unavailable. "
                f"Will retry after {self.recovery_timeout}s"
            )
        
        try:
            result = await func()
            
            # 성공 시 상태 복구
            if self.state == "half_open":
                logger.info("✅ Circuit breaker: Service recovered (closed)")
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(
                f"⚠️  Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}"
            )
            
            # Threshold 초과 시 Open 상태로 전환
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"🔴 Circuit breaker: OPENED due to {self.failure_count} failures. "
                    f"Blocking requests for {self.recovery_timeout}s"
                )
            
            raise

# Global circuit breakers for each service
circuit_breakers: Dict[str, CircuitBreaker] = {
    "edocr2": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "yolo": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "edgnet": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "skinmodel": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "vl": CircuitBreaker(failure_threshold=3, recovery_timeout=120),  # VL API는 더 엄격
}

# =====================
# Health Check with Caching
# =====================

class HealthChecker:
    """서비스 health check with 캐싱"""
    
    def __init__(self, cache_ttl: int = 30):
        self.health_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl
    
    def is_cache_valid(self, service_name: str) -> bool:
        """캐시가 유효한지 확인"""
        if service_name not in self.health_cache:
            return False
        
        entry = self.health_cache[service_name]
        return time.time() - entry['timestamp'] < self.cache_ttl
    
    def get_cached_status(self, service_name: str) -> Optional[bool]:
        """캐시된 health 상태 반환"""
        if self.is_cache_valid(service_name):
            return self.health_cache[service_name]['healthy']
        return None
    
    def set_status(self, service_name: str, is_healthy: bool):
        """Health 상태 캐싱"""
        self.health_cache[service_name] = {
            'healthy': is_healthy,
            'timestamp': time.time()
        }

health_checker = HealthChecker(cache_ttl=30)

