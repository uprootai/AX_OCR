#!/usr/bin/env python3
"""
Gateway API 개선 예제

이 파일은 Gateway API에 새로운 기능들을 통합하는 방법을 보여줍니다.
실제 적용 시 gateway-api/api_server.py에 복사하세요.
"""

import sys
sys.path.insert(0, '/home/uproot/ax/poc')

import httpx
from fastapi import FastAPI, HTTPException, Depends
from typing import Optional

# Import common utilities
from common import (
    retry_async,
    get_circuit_breaker,
    PrometheusMiddleware,
    metrics_endpoint,
    record_request,
    record_error,
    check_rate_limit,
    verify_api_key
)

app = FastAPI(title="Gateway API Enhanced")

# Add Prometheus monitoring
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()


# ============================================================================
# Example 1: Health check with rate limiting (optional)
# ============================================================================

@app.get(
    "/api/v1/health",
    # Uncomment to enable rate limiting
    # dependencies=[Depends(check_rate_limit)]
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Gateway API Enhanced",
        "version": "2.0.0"
    }


# ============================================================================
# Example 2: Protected endpoint with authentication
# ============================================================================

@app.get(
    "/api/v1/protected",
    dependencies=[Depends(verify_api_key)]
)
async def protected_endpoint():
    """
    Protected endpoint requiring API key
    
    Usage:
        curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/protected
    """
    return {"message": "You are authenticated!"}


# ============================================================================
# Example 3: Call external API with Retry + Circuit Breaker
# ============================================================================

async def call_edocr2_with_resilience(file_content: bytes) -> dict:
    """
    Call eDOCr2 API with retry and circuit breaker
    
    This function demonstrates:
    - Exponential backoff retry (3 attempts)
    - Circuit breaker to prevent cascading failures
    - Error tracking for monitoring
    """
    breaker = get_circuit_breaker("edocr2-v1")
    
    async def make_request():
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    "http://localhost:5001/api/v1/ocr",
                    files={"file": ("drawing.pdf", file_content, "application/pdf")},
                    data={"extract_dimensions": "true"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                record_error("edocr2-v1", f"http_{e.response.status_code}")
                raise
            except httpx.RequestError as e:
                record_error("edocr2-v1", "network_error")
                raise
    
    try:
        # Use retry with circuit breaker
        result = await retry_async(
            lambda: breaker.call(make_request),
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            exceptions=(httpx.HTTPError,)
        )
        return result
    except RuntimeError as e:
        # Circuit breaker is open
        raise HTTPException(
            status_code=503,
            detail=f"eDOCr2 service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process drawing: {str(e)}"
        )


@app.post("/api/v1/ocr/resilient")
async def ocr_with_resilience(file: bytes):
    """
    OCR endpoint with retry and circuit breaker
    
    This endpoint automatically:
    - Retries failed requests up to 3 times
    - Opens circuit after 5 consecutive failures
    - Returns 503 if circuit is open
    """
    result = await call_edocr2_with_resilience(file)
    return result


# ============================================================================
# Example 4: Call multiple services in parallel with resilience
# ============================================================================

async def call_service_safe(
    service_name: str,
    url: str,
    file_content: bytes
) -> Optional[dict]:
    """
    Safely call a service with error handling
    
    Returns None if service is unavailable, allowing partial success
    """
    breaker = get_circuit_breaker(service_name)
    
    async def make_request():
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                files={"file": ("drawing.pdf", file_content, "application/pdf")}
            )
            response.raise_for_status()
            return response.json()
    
    try:
        result = await retry_async(
            lambda: breaker.call(make_request),
            max_attempts=2,  # Less retries for parallel calls
            initial_delay=0.5,
            exceptions=(httpx.HTTPError,)
        )
        return result
    except Exception as e:
        # Log error but don't fail entire request
        record_error(service_name, str(type(e).__name__))
        return None


@app.post("/api/v1/process/parallel")
async def process_drawing_parallel(file: bytes):
    """
    Process drawing using multiple services in parallel
    
    This demonstrates:
    - Parallel API calls with asyncio.gather
    - Graceful degradation (partial success allowed)
    - Circuit breaker per service
    """
    import asyncio
    
    # Call services in parallel
    results = await asyncio.gather(
        call_service_safe("edocr2-v1", "http://localhost:5001/api/v1/ocr", file),
        call_service_safe("edgnet", "http://localhost:5012/api/v1/segment", file),
        call_service_safe("skinmodel", "http://localhost:5003/api/v1/predict", file),
        return_exceptions=True  # Don't fail on individual errors
    )
    
    ocr_result, edgnet_result, skinmodel_result = results
    
    return {
        "status": "partial_success" if None in results else "success",
        "ocr": ocr_result if ocr_result else {"error": "Service unavailable"},
        "edgnet": edgnet_result if edgnet_result else {"error": "Service unavailable"},
        "skinmodel": skinmodel_result if skinmodel_result else {"error": "Service unavailable"}
    }


# ============================================================================
# Example 5: Get circuit breaker status
# ============================================================================

@app.get("/api/v1/circuit-breakers")
async def get_circuit_breakers_status():
    """
    Get status of all circuit breakers
    
    Useful for monitoring and debugging
    """
    from common.resilience import CIRCUIT_BREAKERS
    
    return {
        service: breaker.get_status()
        for service, breaker in CIRCUIT_BREAKERS.items()
    }


# ============================================================================
# Usage Instructions
# ============================================================================

if __name__ == "__main__":
    print("""
    ========================================
    Gateway API 개선 예제
    ========================================
    
    이 파일은 다음 기능들의 사용 예제입니다:
    
    1. ✅ Prometheus 모니터링
       - GET /metrics
       - 자동 HTTP 메트릭 수집
    
    2. ✅ API 인증 (선택)
       - GET /api/v1/protected (X-API-Key 필요)
    
    3. ✅ Retry + Circuit Breaker
       - POST /api/v1/ocr/resilient
       - 자동 재시도 (3회, exponential backoff)
       - 서비스 장애 시 circuit open
    
    4. ✅ 병렬 처리
       - POST /api/v1/process/parallel
       - 여러 서비스 동시 호출
       - 부분 성공 허용
    
    5. ✅ Circuit Breaker 모니터링
       - GET /api/v1/circuit-breakers
    
    ========================================
    실제 적용 방법:
    ========================================
    
    1. 이 파일의 함수들을 gateway-api/api_server.py에 복사
    2. 기존 API 호출 부분을 call_service_safe로 교체
    3. PYTHONPATH 설정 또는 common 모듈 복사
    4. 서비스 재시작
    
    ========================================
    테스트 명령어:
    ========================================
    
    # 인증 없이
    curl http://localhost:8000/api/v1/health
    
    # 인증 포함 (ENABLE_AUTH=true인 경우)
    curl -H "X-API-Key: your-key" \\
         http://localhost:8000/api/v1/protected
    
    # Circuit breaker 상태 확인
    curl http://localhost:8000/api/v1/circuit-breakers
    
    # Prometheus 메트릭
    curl http://localhost:8000/metrics
    
    ========================================
    """)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
