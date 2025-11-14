#!/bin/bash

# AX 실증산단 - API 테스트 스크립트
# 전체 시스템 통합 테스트

set -e

echo "==========================================="
echo "AX 실증산단 API 시스템 테스트"
echo "==========================================="
echo ""

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 결과 카운터
PASSED=0
FAILED=0

# 테스트 함수
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got $response)"
        ((FAILED++))
    fi
}

# 1. 헬스체크 테스트
echo "1. Health Check Tests"
echo "-------------------------------------------"

test_endpoint "eDOCr2 API" "http://localhost:5001/api/v1/health" "200"
test_endpoint "EDGNet API" "http://localhost:5002/api/v1/health" "200"
test_endpoint "Skin Model API" "http://localhost:5003/api/v1/health" "200"
test_endpoint "Gateway API" "http://localhost:8000/api/v1/health" "200"

echo ""

# 2. 개별 서비스 기능 테스트
echo "2. Individual Service Tests"
echo "-------------------------------------------"

# 샘플 이미지 경로 (존재하면 테스트)
SAMPLE_IMAGE="/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"

if [ -f "$SAMPLE_IMAGE" ]; then
    echo -n "Testing eDOCr2 OCR endpoint... "
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST http://localhost:5001/api/v1/ocr \
        -F "file=@$SAMPLE_IMAGE" \
        -F "extract_dimensions=true" \
        2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        ((FAILED++))
    fi

    echo -n "Testing EDGNet segment endpoint... "
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST http://localhost:5002/api/v1/segment \
        -F "file=@$SAMPLE_IMAGE" \
        -F "visualize=true" \
        2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP${NC} (Sample image not found: $SAMPLE_IMAGE)"
fi

echo -n "Testing Skin Model tolerance endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:5003/api/v1/tolerance \
    -H "Content-Type: application/json" \
    -d '{
        "dimensions": [{"type": "diameter", "value": 392.0, "tolerance": 0.1}],
        "material": {"name": "Steel"},
        "manufacturing_process": "machining"
    }' \
    2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
    ((FAILED++))
fi

echo ""

# 3. Gateway 통합 테스트
echo "3. Gateway Integration Tests"
echo "-------------------------------------------"

if [ -f "$SAMPLE_IMAGE" ]; then
    echo -n "Testing Gateway process endpoint... "
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST http://localhost:8000/api/v1/process \
        -F "file=@$SAMPLE_IMAGE" \
        -F "use_segmentation=true" \
        -F "use_ocr=true" \
        -F "use_tolerance=true" \
        2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        ((FAILED++))
    fi

    echo -n "Testing Gateway quote endpoint... "
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST http://localhost:8000/api/v1/quote \
        -F "file=@$SAMPLE_IMAGE" \
        -F "material_cost_per_kg=5.0" \
        -F "machining_rate_per_hour=50.0" \
        2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⊘ SKIP${NC} (Sample image not found)"
fi

echo ""

# 4. API 문서 테스트
echo "4. API Documentation Tests"
echo "-------------------------------------------"

test_endpoint "eDOCr2 Swagger UI" "http://localhost:5001/docs" "200"
test_endpoint "EDGNet Swagger UI" "http://localhost:5002/docs" "200"
test_endpoint "Skin Model Swagger UI" "http://localhost:5003/docs" "200"
test_endpoint "Gateway Swagger UI" "http://localhost:8000/docs" "200"

echo ""

# 결과 요약
echo "==========================================="
echo "테스트 결과 요약"
echo "==========================================="
TOTAL=$((PASSED + FAILED))
echo "Total: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 모든 테스트 통과!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ 일부 테스트 실패${NC}"
    exit 1
fi
