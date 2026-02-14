#!/bin/bash
# ============================================================
# Blueprint AI BOM - DSE Bearing 납품 패키지 자동 설치
# 동서기연 터빈 베어링 프로젝트
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_IMAGE="images/blueprint-ai-bom-backend.tar.gz"
FRONTEND_IMAGE="images/blueprint-ai-bom-frontend.tar.gz"
PROJECT_JSON="data/project_dsebearing.json"
BACKEND_URL="http://localhost:5020"
FRONTEND_URL="http://localhost:3000"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo ""
    echo -e "${BLUE}[$1/8]${NC} $2"
    echo "------------------------------------------------------------"
}

print_ok() {
    echo -e "  ${GREEN}OK${NC} $1"
}

print_warn() {
    echo -e "  ${YELLOW}WARNING${NC} $1"
}

print_err() {
    echo -e "  ${RED}ERROR${NC} $1"
}

echo "============================================================"
echo "  Blueprint AI BOM - DSE Bearing 설치"
echo "  동서기연 터빈 베어링 프로젝트"
echo "============================================================"

# ---- Step 1: Docker 이미지 로드 ----
print_step 1 "Docker 이미지 로드"

if [ ! -f "$BACKEND_IMAGE" ]; then
    print_err "$BACKEND_IMAGE 파일을 찾을 수 없습니다."
    exit 1
fi
if [ ! -f "$FRONTEND_IMAGE" ]; then
    print_err "$FRONTEND_IMAGE 파일을 찾을 수 없습니다."
    exit 1
fi

echo "  Backend 이미지 로드 중... (약 2-3분 소요)"
gunzip -c "$BACKEND_IMAGE" | docker load
print_ok "Backend 이미지 로드 완료"

echo "  Frontend 이미지 로드 중..."
gunzip -c "$FRONTEND_IMAGE" | docker load
print_ok "Frontend 이미지 로드 완료"

# ---- Step 2: 데이터 디렉토리 초기화 ----
print_step 2 "데이터 디렉토리 초기화"

mkdir -p data
print_ok "data/ 디렉토리 준비 완료"

# ---- Step 3: 기존 컨테이너 정리 + 서비스 시작 ----
print_step 3 "서비스 시작"

docker compose down 2>/dev/null || true
docker compose up -d
print_ok "컨테이너 시작됨"

# ---- Step 4: 백엔드 헬스체크 대기 ----
print_step 4 "백엔드 헬스체크 대기 (최대 60초)"

MAX_WAIT=60
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
        print_ok "백엔드 정상 응답 (${ELAPSED}초)"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -ne "\r  대기 중... ${ELAPSED}초"
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    print_err "백엔드가 ${MAX_WAIT}초 내에 응답하지 않습니다."
    echo "  docker logs blueprint-ai-bom-backend 명령으로 로그를 확인하세요."
    exit 1
fi

# ---- Step 5: 프로젝트 Import ----
print_step 5 "프로젝트 데이터 Import"

if [ ! -f "$PROJECT_JSON" ]; then
    print_err "$PROJECT_JSON 파일을 찾을 수 없습니다."
    exit 1
fi

IMPORT_RESULT=$(curl -s -X POST "$BACKEND_URL/projects/import" \
    -F "file=@$PROJECT_JSON")

if echo "$IMPORT_RESULT" | grep -q '"project_id"'; then
    print_ok "프로젝트 Import 성공"
else
    print_warn "Import 결과를 확인하세요: $IMPORT_RESULT"
fi

# ---- Step 6: Import 결과 확인 ----
print_step 6 "Import 결과 확인"

PROJECT_ID=$(echo "$IMPORT_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('project_id','N/A'))" 2>/dev/null || echo "N/A")
SESSION_COUNT=$(echo "$IMPORT_RESULT" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('imported_sessions', r.get('sessions_imported', r.get('session_count','N/A'))))" 2>/dev/null || echo "N/A")

echo "  Project ID: $PROJECT_ID"
echo "  Sessions:   $SESSION_COUNT"

# ---- Step 7: 접속 URL 출력 ----
print_step 7 "접속 정보"

echo ""
echo -e "  ${GREEN}Frontend:${NC}  $FRONTEND_URL"
echo -e "  ${GREEN}Backend:${NC}   $BACKEND_URL"
echo -e "  ${GREEN}API Docs:${NC}  $BACKEND_URL/docs"
echo ""

# ---- Step 8: 검증 가이드 ----
print_step 8 "검증 가이드"

echo "  1. 브라우저에서 $FRONTEND_URL 접속"
echo "  2. 프로젝트 목록에서 '동서기연 터빈 베어링' 선택"
echo "  3. BOM 탭: 326개 아이템 확인"
echo "  4. 견적 탭: 총 견적가 ₩100,679,708 확인"
echo "  5. 세션 탭: 53개 분석 세션 확인"
echo ""

echo "============================================================"
echo -e "  ${GREEN}설치 완료!${NC}"
echo "  $FRONTEND_URL 에서 확인하세요."
echo "============================================================"
