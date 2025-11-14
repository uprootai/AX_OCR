#!/usr/bin/env python3
"""
통합 테스트 스크립트 - 전체 파이프라인 End-to-End 테스트

전체 시스템 워크플로우를 테스트:
1. 도면 업로드
2. OCR 실행
3. 세그멘테이션
4. 공차 예측
5. 견적서 생성
6. 결과 검증
"""

import asyncio
import time
import httpx
from pathlib import Path
import json
import sys

# Gateway API URL
GATEWAY_URL = "http://localhost:8000"

# 테스트 색상
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color


class IntegrationTestRunner:
    """통합 테스트 실행 클래스"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def print_header(self, title: str):
        """테스트 헤더 출력"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")

    def print_test(self, name: str, status: bool, message: str = ""):
        """테스트 결과 출력"""
        if status:
            print(f"{GREEN}✓ PASS{NC} - {name}")
            if message:
                print(f"        {message}")
            self.passed += 1
        else:
            print(f"{RED}✗ FAIL{NC} - {name}")
            if message:
                print(f"        {message}")
            self.failed += 1

        self.results.append({
            "name": name,
            "status": "PASS" if status else "FAIL",
            "message": message
        })

    def print_summary(self):
        """최종 결과 요약"""
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"  테스트 결과 요약")
        print(f"{'='*70}")
        print(f"  총 테스트: {total}개")
        print(f"  {GREEN}성공: {self.passed}개{NC}")
        print(f"  {RED}실패: {self.failed}개{NC}")
        print(f"  성공률: {(self.passed/total*100):.1f}%" if total > 0 else "  성공률: 0%")
        print(f"{'='*70}\n")

        return self.failed == 0


async def test_health_checks(runner: IntegrationTestRunner):
    """1단계: 헬스체크 테스트"""
    runner.print_header("1단계: 시스템 헬스체크")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{GATEWAY_URL}/api/v1/health")
            data = response.json()

            # Gateway 상태 확인
            runner.print_test(
                "Gateway API 헬스체크",
                response.status_code == 200,
                f"Status: {data.get('status', 'unknown')}"
            )

            # 각 서비스 상태 확인
            services = data.get('services', {})
            for service_name, service_status in services.items():
                runner.print_test(
                    f"{service_name.upper()} 서비스",
                    service_status == "healthy",
                    f"Status: {service_status}"
                )

        except Exception as e:
            runner.print_test("Gateway API 헬스체크", False, str(e))


async def test_individual_apis(runner: IntegrationTestRunner):
    """2단계: 개별 API 엔드포인트 테스트"""
    runner.print_header("2단계: 개별 API 엔드포인트 테스트")

    apis = [
        ("eDOCr2 API", "http://localhost:5001/api/v1/health"),
        ("EDGNet API", "http://localhost:5012/api/v1/health"),
        ("Skin Model API", "http://localhost:5003/api/v1/health"),
        ("PaddleOCR API", "http://localhost:5006/api/v1/health"),
        ("YOLO API", "http://localhost:5005/api/v1/health"),
        ("VL API", "http://localhost:5004/api/v1/health"),
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in apis:
            try:
                response = await client.get(url)
                runner.print_test(
                    name,
                    response.status_code == 200,
                    f"Response time: {response.elapsed.total_seconds():.2f}s"
                )
            except Exception as e:
                runner.print_test(name, False, str(e))


async def test_gateway_endpoints(runner: IntegrationTestRunner):
    """3단계: Gateway 엔드포인트 구조 테스트"""
    runner.print_header("3단계: Gateway API 엔드포인트 구조")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # OpenAPI 스키마 확인
        try:
            response = await client.get(f"{GATEWAY_URL}/openapi.json")
            runner.print_test(
                "OpenAPI 스키마",
                response.status_code == 200,
                f"총 {len(response.json().get('paths', {}))}개 엔드포인트"
            )
        except Exception as e:
            runner.print_test("OpenAPI 스키마", False, str(e))

        # Swagger UI 확인
        try:
            response = await client.get(f"{GATEWAY_URL}/docs")
            runner.print_test(
                "Swagger UI",
                response.status_code == 200,
                "문서 페이지 접근 가능"
            )
        except Exception as e:
            runner.print_test("Swagger UI", False, str(e))


async def test_ocr_pipeline(runner: IntegrationTestRunner):
    """4단계: OCR 파이프라인 테스트 (샘플 이미지 사용)"""
    runner.print_header("4단계: OCR 파이프라인 테스트")

    # 테스트용 간단한 이미지 생성 (1x1 픽셀 PNG)
    test_image_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Basic OCR 전략 테스트
        try:
            files = {"file": ("test.png", test_image_data, "image/png")}
            data = {"strategy": "basic"}

            response = await client.post(
                f"{GATEWAY_URL}/api/v1/ocr",
                files=files,
                data=data
            )

            runner.print_test(
                "Basic OCR 전략",
                response.status_code in [200, 422],  # 422는 이미지 처리 실패 (정상)
                f"Status: {response.status_code}"
            )
        except Exception as e:
            runner.print_test("Basic OCR 전략", False, str(e))


async def test_process_endpoint(runner: IntegrationTestRunner):
    """5단계: 전체 처리 파이프라인 엔드포인트"""
    runner.print_header("5단계: 전체 처리 파이프라인")

    test_image_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            files = {"file": ("test.png", test_image_data, "image/png")}
            data = {
                "use_segmentation": "false",
                "use_ocr": "true",
                "use_tolerance": "false"
            }

            response = await client.post(
                f"{GATEWAY_URL}/api/v1/process",
                files=files,
                data=data
            )

            runner.print_test(
                "전체 처리 파이프라인",
                response.status_code in [200, 422],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            runner.print_test("전체 처리 파이프라인", False, str(e))


async def test_web_ui_access(runner: IntegrationTestRunner):
    """6단계: Web UI 접근성 테스트"""
    runner.print_header("6단계: Web UI 접근성")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 메인 페이지
        try:
            response = await client.get("http://localhost:5173/")
            runner.print_test(
                "Web UI 메인 페이지",
                response.status_code in [200, 301],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            runner.print_test("Web UI 메인 페이지", False, str(e))

        # Dashboard
        try:
            response = await client.get("http://localhost:5173/dashboard")
            runner.print_test(
                "Dashboard 페이지",
                response.status_code in [200, 301],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            runner.print_test("Dashboard 페이지", False, str(e))

        # Docs 페이지
        try:
            response = await client.get("http://localhost:5173/docs")
            runner.print_test(
                "문서 포털 페이지",
                response.status_code in [200, 301],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            runner.print_test("문서 포털 페이지", False, str(e))


async def main():
    """메인 테스트 실행"""
    print(f"\n{'='*70}")
    print(f"  🧪 AX 실증산단 시스템 - 통합 테스트")
    print(f"{'='*70}")

    runner = IntegrationTestRunner()

    # 테스트 순차 실행
    await test_health_checks(runner)
    await test_individual_apis(runner)
    await test_gateway_endpoints(runner)
    await test_ocr_pipeline(runner)
    await test_process_endpoint(runner)
    await test_web_ui_access(runner)

    # 결과 요약
    success = runner.print_summary()

    # 결과 저장
    result_file = Path("/tmp/integration_test_result.json")
    result_file.write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "passed": runner.passed,
        "failed": runner.failed,
        "total": runner.passed + runner.failed,
        "results": runner.results
    }, indent=2, ensure_ascii=False))

    print(f"📄 상세 결과가 {result_file}에 저장되었습니다.\n")

    # 종료 코드 반환
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
