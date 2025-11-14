#!/usr/bin/env python3
"""
종합 시스템 데모 스크립트

이 스크립트는 개선된 모든 기능을 데모합니다:
1. API 인증
2. Rate limiting
3. Retry logic
4. Circuit breaker
5. Prometheus metrics
6. Multi-service integration
"""

import sys
sys.path.insert(0, '/home/uproot/ax/poc')

import asyncio
import httpx
import time
from pathlib import Path
from typing import Optional


# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


async def demo_health_checks():
    """Demo 1: Health checks for all services"""
    print_section("1️⃣  Health Check - All Services")

    services = [
        ("Gateway API", "http://localhost:8000/api/v1/health"),
        ("eDOCr2 v1", "http://localhost:5001/api/v1/health"),
        ("eDOCr2 v2", "http://localhost:5002/api/v2/health"),
        ("EDGNet", "http://localhost:5012/api/v1/health"),
        ("Skin Model", "http://localhost:5003/api/v1/health"),
        ("Prometheus", "http://localhost:9090/-/healthy"),
        ("Grafana", "http://localhost:3000/api/health"),
    ]

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services:
            try:
                start = time.time()
                response = await client.get(url)
                duration = (time.time() - start) * 1000  # ms

                if response.status_code == 200:
                    print_success(f"{name:<20} - Healthy ({duration:.0f}ms)")
                else:
                    print_error(f"{name:<20} - Unhealthy (HTTP {response.status_code})")
            except Exception as e:
                print_error(f"{name:<20} - Unreachable ({str(e)[:40]})")


async def demo_authentication():
    """Demo 2: API Authentication"""
    print_section("2️⃣  API Authentication")

    # Check if authentication is enabled
    async with httpx.AsyncClient() as client:
        try:
            # Try without API key
            print_info("Attempting request WITHOUT API key...")
            response = await client.get("http://localhost:8000/api/v1/health")

            if response.status_code == 200:
                print_warning("Authentication is DISABLED (ENABLE_AUTH=false)")
                print_info("To enable: Set ENABLE_AUTH=true in .env")
                return

            # Authentication is enabled
            print_success("Authentication is ENABLED")

            # Try with invalid key
            print_info("Attempting request with INVALID API key...")
            response = await client.get(
                "http://localhost:8000/api/v1/health",
                headers={"X-API-Key": "invalid-key"}
            )

            if response.status_code == 403:
                print_success("Invalid key correctly rejected (403)")

            # Try with valid key (if set in environment)
            print_info("Attempting request with VALID API key...")
            import os
            api_key = os.getenv("API_KEY")

            if not api_key:
                print_warning("No API_KEY set in environment")
                return

            response = await client.get(
                "http://localhost:8000/api/v1/health",
                headers={"X-API-Key": api_key}
            )

            if response.status_code == 200:
                print_success("Valid key accepted (200)")

        except Exception as e:
            print_error(f"Authentication test failed: {e}")


async def demo_rate_limiting():
    """Demo 3: Rate Limiting"""
    print_section("3️⃣  Rate Limiting")

    # Check if rate limiting is enabled
    import os
    if os.getenv("ENABLE_RATE_LIMIT", "false").lower() != "true":
        print_warning("Rate limiting is DISABLED (ENABLE_RATE_LIMIT=false)")
        print_info("To enable: Set ENABLE_RATE_LIMIT=true in .env")
        return

    print_success("Rate limiting is ENABLED")

    limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    print_info(f"Limit: {limit_per_minute} requests/minute")

    # Send requests to test rate limiting
    print_info(f"Sending {limit_per_minute + 5} requests...")

    async with httpx.AsyncClient() as client:
        success_count = 0
        blocked_count = 0

        for i in range(limit_per_minute + 5):
            try:
                response = await client.get("http://localhost:8000/api/v1/health")

                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    blocked_count += 1
                    if blocked_count == 1:
                        print_success(f"Request #{i+1} blocked (rate limit exceeded)")
            except Exception:
                pass

        print_info(f"Results: {success_count} allowed, {blocked_count} blocked")

        if blocked_count > 0:
            print_success("Rate limiting is working correctly!")
        else:
            print_warning("No requests were blocked (limit not reached)")


async def demo_retry_logic():
    """Demo 4: Retry Logic"""
    print_section("4️⃣  Retry Logic with Exponential Backoff")

    from common import retry_async

    # Simulate a flaky function
    attempt_count = 0

    async def flaky_api_call():
        nonlocal attempt_count
        attempt_count += 1

        print_info(f"Attempt {attempt_count}...")

        if attempt_count < 3:
            raise httpx.RequestError("Network error (simulated)")

        return {"status": "success", "attempts": attempt_count}

    try:
        result = await retry_async(
            flaky_api_call,
            max_attempts=5,
            initial_delay=0.5,
            max_delay=5.0
        )

        print_success(f"Retry succeeded after {result['attempts']} attempts")
        print_info("Exponential backoff: 0.5s → 1.0s → success")

    except Exception as e:
        print_error(f"Retry failed: {e}")


async def demo_circuit_breaker():
    """Demo 5: Circuit Breaker"""
    print_section("5️⃣  Circuit Breaker Pattern")

    from common import CircuitBreaker

    # Create a circuit breaker
    breaker = CircuitBreaker(
        failure_threshold=3,
        timeout=5.0,
        name="demo-service"
    )

    # Simulate failures
    async def failing_service():
        raise ConnectionError("Service unavailable")

    print_info("Simulating 5 consecutive failures...")

    for i in range(5):
        try:
            async with breaker:
                await failing_service()
        except Exception:
            status = breaker.get_status()
            state_color = {
                "CLOSED": Colors.OKGREEN,
                "OPEN": Colors.FAIL,
                "HALF_OPEN": Colors.WARNING
            }.get(status['state'], Colors.ENDC)

            print(f"{state_color}Attempt {i+1}: {status['state']} "
                  f"(failures: {status['failure_count']}){Colors.ENDC}")

    # Try when circuit is open
    try:
        async with breaker:
            await failing_service()
        print_error("Circuit should have blocked this request!")
    except RuntimeError as e:
        print_success(f"Circuit OPEN - Request correctly blocked")
        print_info(f"Will retry in {breaker.timeout}s (half-open state)")


async def demo_metrics():
    """Demo 6: Prometheus Metrics"""
    print_section("6️⃣  Prometheus Metrics")

    # Check if metrics endpoint is accessible
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/metrics")

            if response.status_code == 200:
                print_success("Metrics endpoint is accessible")

                # Parse some metrics
                metrics_text = response.text
                lines = metrics_text.split('\n')

                # Find interesting metrics
                print_info("\nSample metrics:")

                for line in lines:
                    if line.startswith('http_requests_total'):
                        print(f"  {line}")
                    elif line.startswith('http_request_duration_seconds_count'):
                        print(f"  {line}")
                        break

                print_info("\nFull metrics available at: http://localhost:8000/metrics")
                print_info("Prometheus UI: http://localhost:9090")
                print_info("Grafana UI: http://localhost:3000")
            else:
                print_warning("Metrics endpoint not enabled")

        except Exception as e:
            print_error(f"Could not access metrics: {e}")


async def demo_circuit_breaker_status():
    """Demo 7: Circuit Breaker Status Monitoring"""
    print_section("7️⃣  Circuit Breaker Status")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/v1/circuit-breakers")

            if response.status_code == 200:
                breakers = response.json()

                if not breakers:
                    print_warning("No circuit breakers registered yet")
                    print_info("Circuit breakers are created on first use")
                    return

                print_success("Circuit breaker status:")
                print()

                for service, status in breakers.items():
                    state = status['state']
                    state_color = {
                        "CLOSED": Colors.OKGREEN,
                        "OPEN": Colors.FAIL,
                        "HALF_OPEN": Colors.WARNING
                    }.get(state, Colors.ENDC)

                    print(f"  {service}:")
                    print(f"    State: {state_color}{state}{Colors.ENDC}")
                    print(f"    Failures: {status['failure_count']}")
                    print(f"    Last failure: {status['last_failure_time'] or 'None'}")
                    print()
            else:
                print_warning("Circuit breaker status endpoint not available")

        except Exception as e:
            print_error(f"Could not get circuit breaker status: {e}")


async def demo_full_pipeline(test_file: Optional[Path] = None):
    """Demo 8: Full OCR Pipeline with Resilience"""
    print_section("8️⃣  Full OCR Pipeline (with Retry + Circuit Breaker)")

    if not test_file or not test_file.exists():
        print_warning("No test file available - skipping pipeline demo")
        print_info("To test: provide a drawing file in /home/uproot/ax/poc/test_data/")
        return

    print_info(f"Processing: {test_file.name}")

    from common import retry_async, get_circuit_breaker

    breaker = get_circuit_breaker("edocr2-v1")

    async def call_ocr():
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(test_file, 'rb') as f:
                response = await client.post(
                    "http://localhost:5001/api/v1/ocr",
                    files={"file": f},
                    data={"extract_dimensions": "true"}
                )
                response.raise_for_status()
                return response.json()

    try:
        start = time.time()

        # Use retry + circuit breaker
        result = await retry_async(
            lambda: breaker.call(call_ocr),
            max_attempts=3,
            initial_delay=1.0
        )

        duration = time.time() - start

        print_success(f"OCR completed in {duration:.2f}s")

        # Show results
        dimensions = result.get('dimensions', [])
        gdt = result.get('gdt', [])

        print_info(f"Extracted: {len(dimensions)} dimensions, {len(gdt)} GD&T symbols")

    except Exception as e:
        print_error(f"OCR failed: {str(e)[:100]}")


async def main():
    """Run all demos"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("   AX 도면 분석 시스템 - Enhanced Features Demo")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print_info("This demo showcases all improved features:")
    print("  1. Health checks")
    print("  2. API authentication")
    print("  3. Rate limiting")
    print("  4. Retry logic")
    print("  5. Circuit breaker")
    print("  6. Prometheus metrics")
    print("  7. Circuit breaker monitoring")
    print("  8. Full OCR pipeline with resilience")

    # Find test file
    test_file = None
    possible_paths = [
        Path("/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"),
        Path("/home/uproot/ax/poc/test_data/sample.pdf"),
        Path("/home/uproot/ax/poc/test_data/sample.jpg"),
    ]

    for path in possible_paths:
        if path.exists():
            test_file = path
            break

    # Run demos
    await demo_health_checks()
    await demo_authentication()
    await demo_rate_limiting()
    await demo_retry_logic()
    await demo_circuit_breaker()
    await demo_metrics()
    await demo_circuit_breaker_status()
    await demo_full_pipeline(test_file)

    # Final summary
    print_section("✅ Demo Complete!")

    print_info("Next steps:")
    print("  1. Check Prometheus: http://localhost:9090")
    print("  2. Setup Grafana dashboard: http://localhost:3000")
    print("  3. Review integration guide: TODO/INTEGRATION_GUIDE.md")
    print("  4. Customize security: security_config.yaml")

    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


if __name__ == "__main__":
    asyncio.run(main())
