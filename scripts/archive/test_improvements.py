#!/usr/bin/env python3
"""
개선 사항 테스트 스크립트

모든 새로운 기능 (인증, Rate limiting, Retry, Circuit breaker, Monitoring)을 테스트합니다.
"""

import sys
sys.path.insert(0, '/home/uproot/ax/poc')

import asyncio
import httpx
from common import (
    retry_async,
    with_retry,
    CircuitBreaker,
    get_circuit_breaker,
    rate_limiter
)


async def test_retry_logic():
    """Test retry mechanism"""
    print("\n=== 1. Retry Logic 테스트 ===\n")
    
    # Simulated failing function
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Failed attempt {attempt_count}")
        return "Success!"
    
    try:
        result = await retry_async(
            flaky_function,
            max_attempts=3,
            initial_delay=0.1
        )
        print(f"✅ Retry succeeded: {result}")
        print(f"   Took {attempt_count} attempts")
    except Exception as e:
        print(f"❌ Retry failed: {e}")


async def test_circuit_breaker():
    """Test circuit breaker"""
    print("\n=== 2. Circuit Breaker 테스트 ===\n")
    
    breaker = CircuitBreaker(
        failure_threshold=3,
        timeout=2.0,
        name="test-service"
    )
    
    # Simulate failures
    async def failing_service():
        raise ConnectionError("Service unavailable")
    
    # Trigger failures to open circuit
    for i in range(5):
        try:
            async with breaker:
                await failing_service()
        except Exception as e:
            status = breaker.get_status()
            print(f"Attempt {i+1}: {status['state']} (failures: {status['failure_count']})")
    
    # Try when circuit is open
    try:
        async with breaker:
            await failing_service()
    except RuntimeError as e:
        print(f"✅ Circuit correctly blocked request: {str(e)[:80]}")


async def test_rate_limiter():
    """Test rate limiter"""
    print("\n=== 3. Rate Limiter 테스트 ===\n")
    
    client_ip = "127.0.0.1"
    
    # Enable rate limiting for test
    import os
    os.environ["ENABLE_RATE_LIMIT"] = "true"
    os.environ["RATE_LIMIT_PER_MINUTE"] = "5"
    
    # Reinitialize rate limiter
    from common.rate_limiter import rate_limiter
    
    # Send requests
    for i in range(7):
        is_allowed, limit_type = rate_limiter.check_rate_limit(client_ip)
        if is_allowed:
            rate_limiter.record_request(client_ip)
            print(f"Request {i+1}: ✅ Allowed")
        else:
            print(f"Request {i+1}: ❌ Blocked ({limit_type})")


async def test_api_auth():
    """Test API authentication"""
    print("\n=== 4. API Authentication 테스트 ===\n")
    
    # Mock setup
    from common.auth import VALID_API_KEYS
    VALID_API_KEYS.clear()
    VALID_API_KEYS["test-key-123"] = "test-client"
    
    import os
    os.environ["ENABLE_AUTH"] = "true"
    
    # Test valid key
    from common.auth import verify_api_key
    from fastapi.security import APIKeyHeader
    
    try:
        client = await verify_api_key("test-key-123")
        print(f"✅ Valid API key accepted: {client}")
    except Exception as e:
        print(f"❌ Valid key rejected: {e}")
    
    # Test invalid key
    try:
        await verify_api_key("invalid-key")
        print("❌ Invalid key was accepted (should have failed)")
    except Exception as e:
        print(f"✅ Invalid key correctly rejected")


async def test_service_integration():
    """Test real service with improvements"""
    print("\n=== 5. 실제 서비스 통합 테스트 ===\n")
    
    breaker = get_circuit_breaker("gateway")
    
    async def call_gateway_health():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/health")
            return response.json()
    
    try:
        # Use retry + circuit breaker
        result = await retry_async(
            lambda: breaker.call(call_gateway_health),
            max_attempts=3
        )
        print(f"✅ Gateway health: {result.get('status')}")
    except Exception as e:
        print(f"❌ Failed to call gateway: {e}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("       개선 사항 테스트 스위트")
    print("=" * 60)
    
    await test_retry_logic()
    await test_circuit_breaker()
    await test_rate_limiter()
    await test_api_auth()
    await test_service_integration()
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
