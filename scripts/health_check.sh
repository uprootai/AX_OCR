#!/bin/bash
# AI Drawing Analysis System - 헬스 체크 스크립트
# 시스템 전체 상태 점검

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
WARN=0
FAIL=0

check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL++))
}

echo "============================================"
echo "🏥 시스템 헬스 체크"
echo "============================================"
echo ""
echo "점검 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Docker 서비스 상태
echo "1. Docker 서비스 상태"
echo "----------------------------------------"

if systemctl is-active --quiet docker; then
    check_pass "Docker 데몬 실행 중"
else
    check_fail "Docker 데몬이 실행되지 않음"
fi

echo ""

# 2. Docker 컨테이너 상태
echo "2. Docker 컨테이너 상태"
echo "----------------------------------------"

cd "$PROJECT_ROOT"

EXPECTED_SERVICES=("web-ui" "gateway" "edocr2" "yolo" "edgnet" "skinmodel" "vl" "paddleocr" "admin-dashboard")

for service in "${EXPECTED_SERVICES[@]}"; do
    if docker-compose ps | grep "$service" | grep -q "Up"; then
        # 컨테이너 헬스 확인
        CONTAINER_ID=$(docker-compose ps -q "$service")
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_ID" 2>/dev/null || echo "none")

        if [ "$HEALTH_STATUS" == "healthy" ]; then
            check_pass "$service (healthy)"
        elif [ "$HEALTH_STATUS" == "none" ]; then
            check_pass "$service (running, no health check)"
        else
            check_warn "$service (running, health: $HEALTH_STATUS)"
        fi
    else
        check_fail "$service (not running)"
    fi
done

echo ""

# 3. API 엔드포인트 응답 확인
echo "3. API 엔드포인트 응답 확인"
echo "----------------------------------------"

API_ENDPOINTS=(
    "Gateway:http://localhost:8000/health"
    "eDOCr2:http://localhost:8001/health"
    "YOLO:http://localhost:8002/health"
    "EDGNet:http://localhost:8003/health"
    "SkinModel:http://localhost:8004/health"
    "VL:http://localhost:8005/health"
    "PaddleOCR:http://localhost:8006/health"
    "Admin:http://localhost:8007/api/status"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    name="${endpoint%%:*}"
    url="${endpoint#*:}"

    if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" | grep -q "200"; then
        check_pass "$name API responding"
    else
        check_fail "$name API not responding ($url)"
    fi
done

echo ""

# 4. GPU 상태 (있는 경우)
echo "4. GPU 상태"
echo "----------------------------------------"

if command -v nvidia-smi &> /dev/null; then
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
    GPU_MEM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
    GPU_MEM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1)

    echo "  GPU 사용률: ${GPU_UTIL}%"
    echo "  GPU 메모리: ${GPU_MEM_USED}MB / ${GPU_MEM_TOTAL}MB"
    echo "  GPU 온도: ${GPU_TEMP}°C"

    if [ "$GPU_TEMP" -lt 80 ]; then
        check_pass "GPU 온도 정상 (${GPU_TEMP}°C)"
    else
        check_warn "GPU 온도 높음 (${GPU_TEMP}°C)"
    fi

    GPU_MEM_PERCENT=$((GPU_MEM_USED * 100 / GPU_MEM_TOTAL))
    if [ "$GPU_MEM_PERCENT" -lt 90 ]; then
        check_pass "GPU 메모리 여유 있음 (${GPU_MEM_PERCENT}% 사용)"
    else
        check_warn "GPU 메모리 부족 (${GPU_MEM_PERCENT}% 사용)"
    fi
else
    check_warn "GPU 없음 (CPU 모드)"
fi

echo ""

# 5. 시스템 리소스
echo "5. 시스템 리소스"
echo "----------------------------------------"

# CPU 사용률
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "  CPU 사용률: ${CPU_USAGE}%"

if (( $(echo "$CPU_USAGE < 80" | bc -l) )); then
    check_pass "CPU 사용률 정상 (${CPU_USAGE}%)"
else
    check_warn "CPU 사용률 높음 (${CPU_USAGE}%)"
fi

# 메모리 사용률
MEM_TOTAL=$(free -g | awk '/^Mem:/{print $2}')
MEM_USED=$(free -g | awk '/^Mem:/{print $3}')
MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))

echo "  메모리 사용: ${MEM_USED}GB / ${MEM_TOTAL}GB (${MEM_PERCENT}%)"

if [ "$MEM_PERCENT" -lt 85 ]; then
    check_pass "메모리 사용률 정상 (${MEM_PERCENT}%)"
else
    check_warn "메모리 사용률 높음 (${MEM_PERCENT}%)"
fi

# 디스크 사용률
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
echo "  디스크 사용률: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -lt 85 ]; then
    check_pass "디스크 공간 충분 (${DISK_USAGE}% 사용)"
else
    check_warn "디스크 공간 부족 (${DISK_USAGE}% 사용)"
fi

echo ""

# 6. AI 모델 파일 확인
echo "6. AI 모델 파일 확인"
echo "----------------------------------------"

MODEL_DIRS=(
    "edocr2-api/models"
    "yolo-api/models"
    "edgnet-api/models"
    "skinmodel-api/models"
    "vl-api/models"
    "paddleocr-api/models"
)

for model_dir in "${MODEL_DIRS[@]}"; do
    api_name=$(echo "$model_dir" | cut -d'/' -f1 | sed 's/-api//')

    if [ -d "${PROJECT_ROOT}/${model_dir}" ]; then
        model_count=$(find "${PROJECT_ROOT}/${model_dir}" -type f \( -name "*.pth" -o -name "*.pt" -o -name "*.pkl" -o -name "*.h5" \) 2>/dev/null | wc -l)

        if [ "$model_count" -gt 0 ]; then
            check_pass "$api_name: $model_count model(s) found"
        else
            check_warn "$api_name: No models found"
        fi
    else
        check_fail "$api_name: Model directory not found"
    fi
done

echo ""

# 7. 로그 파일 크기 확인
echo "7. 로그 파일 상태"
echo "----------------------------------------"

if [ -d "${PROJECT_ROOT}/logs" ]; then
    LOG_SIZE=$(du -sh "${PROJECT_ROOT}/logs" 2>/dev/null | cut -f1)
    LOG_COUNT=$(find "${PROJECT_ROOT}/logs" -type f 2>/dev/null | wc -l)

    echo "  로그 파일: $LOG_COUNT 개"
    echo "  로그 크기: $LOG_SIZE"

    # 로그 파일 크기를 바이트로 변환하여 확인 (간단한 체크)
    LOG_SIZE_MB=$(du -sm "${PROJECT_ROOT}/logs" 2>/dev/null | cut -f1)

    if [ "$LOG_SIZE_MB" -lt 1000 ]; then
        check_pass "로그 크기 정상 ($LOG_SIZE)"
    else
        check_warn "로그 크기 큼 ($LOG_SIZE) - 정리 권장"
    fi
else
    check_warn "로그 디렉토리 없음"
fi

echo ""

# 8. 네트워크 포트 확인
echo "8. 네트워크 포트 상태"
echo "----------------------------------------"

PORTS=(5173 8000 8001 8002 8003 8004 8005 8006 8007)

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
        check_pass "Port $port: Listening"
    else
        check_fail "Port $port: Not listening"
    fi
done

echo ""

# 9. Docker 이미지 상태
echo "9. Docker 이미지 상태"
echo "----------------------------------------"

REQUIRED_IMAGES=(
    "poc_web-ui:latest"
    "poc_gateway:latest"
    "poc_edocr2:latest"
    "poc_yolo:latest"
    "poc_edgnet:latest"
    "poc_skinmodel:latest"
    "poc_vl:latest"
    "poc_paddleocr:latest"
    "poc_admin-dashboard:latest"
)

for image in "${REQUIRED_IMAGES[@]}"; do
    if docker image inspect "$image" > /dev/null 2>&1; then
        IMAGE_SIZE=$(docker image inspect "$image" --format='{{.Size}}' | awk '{print $1/1024/1024}')
        check_pass "$image (${IMAGE_SIZE%.*}MB)"
    else
        check_fail "$image not found"
    fi
done

echo ""

# 10. 최근 에러 로그 확인
echo "10. 최근 에러 로그"
echo "----------------------------------------"

if [ -d "${PROJECT_ROOT}/logs" ]; then
    RECENT_ERRORS=$(find "${PROJECT_ROOT}/logs" -type f -mtime -1 -exec grep -i "error\|exception\|critical" {} \; 2>/dev/null | wc -l)

    echo "  최근 24시간 에러: $RECENT_ERRORS 건"

    if [ "$RECENT_ERRORS" -eq 0 ]; then
        check_pass "최근 에러 없음"
    elif [ "$RECENT_ERRORS" -lt 10 ]; then
        check_warn "최근 에러 $RECENT_ERRORS 건 발견"
    else
        check_fail "최근 에러 $RECENT_ERRORS 건 발견 - 확인 필요"
    fi
fi

echo ""

# 최종 결과
echo "============================================"
echo "📊 헬스 체크 결과"
echo "============================================"
echo ""
echo -e "${GREEN}PASS: $PASS${NC}"
echo -e "${YELLOW}WARN: $WARN${NC}"
echo -e "${RED}FAIL: $FAIL${NC}"
echo ""

# 전체 점수 계산
TOTAL=$((PASS + WARN + FAIL))
if [ "$TOTAL" -gt 0 ]; then
    HEALTH_SCORE=$((PASS * 100 / TOTAL))
    echo "시스템 상태 점수: ${HEALTH_SCORE}%"
    echo ""

    if [ "$HEALTH_SCORE" -ge 90 ]; then
        echo -e "${GREEN}✅ 시스템이 정상적으로 작동하고 있습니다!${NC}"
        EXIT_CODE=0
    elif [ "$HEALTH_SCORE" -ge 70 ]; then
        echo -e "${YELLOW}⚠️  일부 경고가 있지만 시스템은 작동합니다.${NC}"
        echo "   WARN 및 FAIL 항목을 확인하세요."
        EXIT_CODE=1
    else
        echo -e "${RED}❌ 시스템에 심각한 문제가 있습니다!${NC}"
        echo "   FAIL 항목을 즉시 확인하세요."
        EXIT_CODE=2
    fi
fi

echo ""
echo "============================================"
echo "💡 권장 사항"
echo "============================================"
echo ""

if [ "$WARN" -gt 0 ] || [ "$FAIL" -gt 0 ]; then
    echo "문제 해결:"
    echo "  - 로그 확인: docker-compose logs [service_name]"
    echo "  - 서비스 재시작: docker-compose restart [service_name]"
    echo "  - 전체 재시작: docker-compose down && docker-compose up -d"
    echo ""
fi

if [ "$LOG_SIZE_MB" -gt 500 ]; then
    echo "로그 정리:"
    echo "  - 오래된 로그 삭제: find logs/ -mtime +30 -delete"
    echo ""
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "디스크 공간 확보:"
    echo "  - Docker 정리: docker system prune -a"
    echo "  - 백업 정리: find backups/ -mtime +30 -delete"
    echo ""
fi

echo "정기 점검:"
echo "  - 매일: bash scripts/health_check.sh"
echo "  - 매주: bash scripts/backup.sh"
echo "  - 매월: 시스템 업데이트 및 모델 재학습 검토"
echo ""

# 헬스 체크 로그 저장
HEALTH_LOG="${PROJECT_ROOT}/logs/health_check_$(date '+%Y%m%d_%H%M%S').log"
mkdir -p "${PROJECT_ROOT}/logs"

{
    echo "Health Check Report"
    echo "==================="
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Results:"
    echo "  PASS: $PASS"
    echo "  WARN: $WARN"
    echo "  FAIL: $FAIL"
    echo "  Score: ${HEALTH_SCORE}%"
    echo ""
} > "$HEALTH_LOG"

echo "헬스 체크 로그 저장: $HEALTH_LOG"
echo ""

exit $EXIT_CODE
