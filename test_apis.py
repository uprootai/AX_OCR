#!/usr/bin/env python3
"""
AX 실증산단 - API 테스트 스크립트 (Python)
전체 시스템 통합 테스트
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, Tuple

# 색상 코드
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

# API URLs
EDOCR2_URL = "http://localhost:5001"
EDGNET_URL = "http://localhost:5012"  # Note: Changed from 5002 due to port conflict
SKINMODEL_URL = "http://localhost:5003"
GATEWAY_URL = "http://localhost:8000"

# 샘플 이미지 경로
SAMPLE_IMAGE = Path("/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg")

# 테스트 결과
passed = 0
failed = 0


def print_header(text: str):
    """헤더 출력"""
    print(f"\n{'=' * 60}")
    print(text)
    print('=' * 60)


def print_section(text: str):
    """섹션 출력"""
    print(f"\n{text}")
    print('-' * 60)


def test_endpoint(name: str, url: str, expected_status: int = 200) -> bool:
    """
    엔드포인트 테스트

    Args:
        name: 테스트 이름
        url: 테스트할 URL
        expected_status: 기대하는 HTTP 상태 코드

    Returns:
        bool: 테스트 성공 여부
    """
    global passed, failed

    print(f"Testing {name}... ", end='', flush=True)

    try:
        response = requests.get(url, timeout=10)
        status = response.status_code

        if status == expected_status:
            print(f"{GREEN}✓ PASS{NC} (HTTP {status})")
            passed += 1
            return True
        else:
            print(f"{RED}✗ FAIL{NC} (Expected HTTP {expected_status}, got {status})")
            failed += 1
            return False

    except Exception as e:
        print(f"{RED}✗ FAIL{NC} (Error: {str(e)})")
        failed += 1
        return False


def test_post_endpoint(name: str, url: str, files: Dict = None, data: Dict = None, json_data: Dict = None) -> Tuple[bool, Dict]:
    """
    POST 엔드포인트 테스트

    Args:
        name: 테스트 이름
        url: 테스트할 URL
        files: 업로드할 파일
        data: Form 데이터
        json_data: JSON 데이터

    Returns:
        Tuple[bool, Dict]: (성공 여부, 응답 데이터)
    """
    global passed, failed

    print(f"Testing {name}... ", end='', flush=True)

    try:
        if json_data:
            response = requests.post(url, json=json_data, timeout=60)
        else:
            response = requests.post(url, files=files, data=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            print(f"{GREEN}✓ PASS{NC} (Time: {result.get('processing_time', 'N/A')}s)")
            passed += 1
            return True, result
        else:
            print(f"{RED}✗ FAIL{NC} (HTTP {response.status_code})")
            failed += 1
            return False, {}

    except Exception as e:
        print(f"{RED}✗ FAIL{NC} (Error: {str(e)})")
        failed += 1
        return False, {}


def main():
    """메인 테스트 실행"""
    print_header("AX 실증산단 API 시스템 테스트")

    # 1. 헬스체크 테스트
    print_section("1. Health Check Tests")
    test_endpoint("eDOCr2 API", f"{EDOCR2_URL}/api/v1/health")
    test_endpoint("EDGNet API", f"{EDGNET_URL}/api/v1/health")
    test_endpoint("Skin Model API", f"{SKINMODEL_URL}/api/v1/health")
    test_endpoint("Gateway API", f"{GATEWAY_URL}/api/v1/health")

    # 2. 개별 서비스 기능 테스트
    print_section("2. Individual Service Tests")

    if SAMPLE_IMAGE.exists():
        # eDOCr2 OCR 테스트
        with open(SAMPLE_IMAGE, 'rb') as f:
            files = {'file': f}
            data = {
                'extract_dimensions': True,
                'extract_gdt': True,
                'extract_text': True
            }
            success, result = test_post_endpoint(
                "eDOCr2 OCR",
                f"{EDOCR2_URL}/api/v1/ocr",
                files=files,
                data=data
            )

            if success:
                ocr_data = result.get('data', {})
                print(f"   - Dimensions: {len(ocr_data.get('dimensions', []))}")
                print(f"   - GD&T: {len(ocr_data.get('gdt', []))}")

        # EDGNet 세그멘테이션 테스트
        with open(SAMPLE_IMAGE, 'rb') as f:
            files = {'file': f}
            data = {'visualize': True, 'num_classes': 3}
            success, result = test_post_endpoint(
                "EDGNet Segmentation",
                f"{EDGNET_URL}/api/v1/segment",
                files=files,
                data=data
            )

            if success:
                seg_data = result.get('data', {})
                print(f"   - Components: {seg_data.get('num_components', 0)}")
                classifications = seg_data.get('classifications', {})
                print(f"   - Contours: {classifications.get('contour', 0)}")
                print(f"   - Text: {classifications.get('text', 0)}")
                print(f"   - Dimensions: {classifications.get('dimension', 0)}")
    else:
        print(f"{YELLOW}⊘ SKIP{NC} (Sample image not found: {SAMPLE_IMAGE})")

    # Skin Model 공차 예측 테스트
    json_data = {
        "dimensions": [
            {"type": "diameter", "value": 392.0, "tolerance": 0.1, "unit": "mm"}
        ],
        "material": {"name": "Steel"},
        "manufacturing_process": "machining"
    }
    success, result = test_post_endpoint(
        "Skin Model Tolerance",
        f"{SKINMODEL_URL}/api/v1/tolerance",
        json_data=json_data
    )

    if success:
        tol_data = result.get('data', {})
        predicted = tol_data.get('predicted_tolerances', {})
        print(f"   - Flatness: {predicted.get('flatness', 0)}")
        print(f"   - Cylindricity: {predicted.get('cylindricity', 0)}")
        manufact = tol_data.get('manufacturability', {})
        print(f"   - Difficulty: {manufact.get('difficulty', 'N/A')}")

    # 3. Gateway 통합 테스트
    print_section("3. Gateway Integration Tests")

    if SAMPLE_IMAGE.exists():
        # Gateway 전체 파이프라인
        with open(SAMPLE_IMAGE, 'rb') as f:
            files = {'file': f}
            data = {
                'use_segmentation': True,
                'use_ocr': True,
                'use_tolerance': True
            }
            success, result = test_post_endpoint(
                "Gateway Process",
                f"{GATEWAY_URL}/api/v1/process",
                files=files,
                data=data
            )

            if success:
                pipeline_data = result.get('data', {})
                print(f"   - Segmentation: {'✓' if pipeline_data.get('segmentation') else '✗'}")
                print(f"   - OCR: {'✓' if pipeline_data.get('ocr') else '✗'}")
                print(f"   - Tolerance: {'✓' if pipeline_data.get('tolerance') else '✗'}")

        # Gateway 견적 생성
        with open(SAMPLE_IMAGE, 'rb') as f:
            files = {'file': f}
            data = {
                'material_cost_per_kg': 5.0,
                'machining_rate_per_hour': 50.0,
                'tolerance_premium_factor': 1.2
            }
            success, result = test_post_endpoint(
                "Gateway Quote",
                f"{GATEWAY_URL}/api/v1/quote",
                files=files,
                data=data
            )

            if success:
                quote = result.get('data', {}).get('quote', {})
                breakdown = quote.get('breakdown', {})
                print(f"   - Total Cost: ${breakdown.get('total', 0):.2f}")
                print(f"   - Material: ${breakdown.get('material_cost', 0):.2f}")
                print(f"   - Machining: ${breakdown.get('machining_cost', 0):.2f}")
                print(f"   - Lead Time: {quote.get('lead_time_days', 0)} days")
    else:
        print(f"{YELLOW}⊘ SKIP{NC} (Sample image not found)")

    # 4. API 문서 테스트
    print_section("4. API Documentation Tests")
    test_endpoint("eDOCr2 Swagger UI", f"{EDOCR2_URL}/docs")
    test_endpoint("EDGNet Swagger UI", f"{EDGNET_URL}/docs")
    test_endpoint("Skin Model Swagger UI", f"{SKINMODEL_URL}/docs")
    test_endpoint("Gateway Swagger UI", f"{GATEWAY_URL}/docs")

    # 결과 요약
    print_header("테스트 결과 요약")
    total = passed + failed
    print(f"Total: {total}")
    print(f"{GREEN}Passed: {passed}{NC}")
    print(f"{RED}Failed: {failed}{NC}")

    if failed == 0:
        print(f"\n{GREEN}✓ 모든 테스트 통과!{NC}")
        return 0
    else:
        print(f"\n{RED}✗ 일부 테스트 실패{NC}")
        return 1


if __name__ == "__main__":
    exit(main())
