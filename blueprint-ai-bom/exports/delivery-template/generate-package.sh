#!/bin/bash
# ============================================================
# Blueprint AI BOM - 납품 패키지 생성기
# 사용법: ./generate-package.sh --customer-id <id> --customer-name <name> ...
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPORTS_DIR="$(dirname "$SCRIPT_DIR")"

# ---- 색상 정의 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_ok()   { echo -e "  ${GREEN}OK${NC} $1"; }
print_err()  { echo -e "  ${RED}ERROR${NC} $1"; exit 1; }
print_info() { echo -e "  ${BLUE}INFO${NC} $1"; }

# ---- 인수 파싱 ----
CUSTOMER_ID=""
CUSTOMER_NAME=""
PROJECT_NAME=""
PROJECT_JSON=""
SESSION_COUNT=""
BOM_COUNT=""
TOTAL_QUOTE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --customer-id)    CUSTOMER_ID="$2";    shift 2 ;;
        --customer-name)  CUSTOMER_NAME="$2";  shift 2 ;;
        --project-name)   PROJECT_NAME="$2";   shift 2 ;;
        --project-json)   PROJECT_JSON="$2";   shift 2 ;;
        --session-count)  SESSION_COUNT="$2";  shift 2 ;;
        --bom-count)      BOM_COUNT="$2";      shift 2 ;;
        --total-quote)    TOTAL_QUOTE="$2";    shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ---- 필수 인수 검증 ----
[ -z "$CUSTOMER_ID" ]   && print_err "--customer-id 가 필요합니다. (예: dsebearing)"
[ -z "$CUSTOMER_NAME" ] && print_err "--customer-name 이 필요합니다. (예: 동서기연)"
[ -z "$PROJECT_NAME" ]  && print_err "--project-name 이 필요합니다. (예: 터빈 베어링)"
[ -z "$SESSION_COUNT" ] && print_err "--session-count 가 필요합니다. (예: 53)"
[ -z "$BOM_COUNT" ]     && print_err "--bom-count 가 필요합니다. (예: 326)"
[ -z "$TOTAL_QUOTE" ]   && print_err "--total-quote 가 필요합니다. (예: ₩100,679,708)"

# ---- 출력 디렉토리 설정 ----
OUT_DIR="$EXPORTS_DIR/${CUSTOMER_ID}-delivery"

echo "============================================================"
echo "  Blueprint AI BOM 납품 패키지 생성기"
echo "============================================================"
echo "  Customer ID:   $CUSTOMER_ID"
echo "  Customer Name: $CUSTOMER_NAME"
echo "  Project Name:  $PROJECT_NAME"
echo "  Session Count: $SESSION_COUNT"
echo "  BOM Count:     $BOM_COUNT"
echo "  Total Quote:   $TOTAL_QUOTE"
echo "  Output Dir:    $OUT_DIR"
echo "============================================================"
echo ""

# ---- Step 1: 출력 디렉토리 생성 ----
print_info "Step 1: 출력 디렉토리 생성"
mkdir -p "$OUT_DIR/images"
mkdir -p "$OUT_DIR/data"
print_ok "디렉토리 생성: $OUT_DIR"

# ---- Step 2: 템플릿 처리 함수 ----
# sed에서 & / \ 는 특수문자 — 치환값에서 이스케이프 필요
sed_escape() {
    printf '%s' "$1" | sed 's/[&\\/]/\\&/g'
}

process_template() {
    local src="$1"
    local dst="$2"
    sed \
        -e "s|{{CUSTOMER_ID}}|$(sed_escape "${CUSTOMER_ID}")|g" \
        -e "s|{{CUSTOMER_NAME}}|$(sed_escape "${CUSTOMER_NAME}")|g" \
        -e "s|{{PROJECT_NAME}}|$(sed_escape "${PROJECT_NAME}")|g" \
        -e "s|{{SESSION_COUNT}}|$(sed_escape "${SESSION_COUNT}")|g" \
        -e "s|{{BOM_COUNT}}|$(sed_escape "${BOM_COUNT}")|g" \
        -e "s|{{TOTAL_QUOTE}}|$(sed_escape "${TOTAL_QUOTE}")|g" \
        "$src" > "$dst"
}

# ---- Step 3: 템플릿 파일 처리 ----
print_info "Step 2: 템플릿 파일 처리"

process_template "$SCRIPT_DIR/docker-compose.yml.template" "$OUT_DIR/docker-compose.yml"
print_ok "docker-compose.yml 생성"

process_template "$SCRIPT_DIR/setup.sh.template" "$OUT_DIR/setup.sh"
print_ok "setup.sh 생성"

process_template "$SCRIPT_DIR/setup.ps1.template" "$OUT_DIR/setup.ps1"
print_ok "setup.ps1 생성"

process_template "$SCRIPT_DIR/README.md.template" "$OUT_DIR/README.md"
print_ok "README.md 생성"

# ---- Step 4: 실행 권한 설정 ----
print_info "Step 3: 실행 권한 설정"
chmod +x "$OUT_DIR/setup.sh"
print_ok "setup.sh 실행 권한 설정"

# ---- Step 5: 프로젝트 JSON 복사 ----
print_info "Step 4: 프로젝트 JSON 복사"
if [ -n "$PROJECT_JSON" ] && [ -f "$PROJECT_JSON" ]; then
    cp "$PROJECT_JSON" "$OUT_DIR/data/project_${CUSTOMER_ID}.json"
    print_ok "프로젝트 JSON 복사: $PROJECT_JSON"
else
    echo -e "  ${YELLOW}SKIP${NC} --project-json 미지정 또는 파일 없음 — data/ 는 수동으로 채우세요."
fi

# ---- Step 6: Docker 이미지 복사 ----
print_info "Step 5: Docker 이미지 복사"
SHARED_IMAGES="$EXPORTS_DIR/dsebearing-delivery/images"
if [ -d "$SHARED_IMAGES" ]; then
    for img in "$SHARED_IMAGES"/*.tar.gz; do
        [ -f "$img" ] || continue
        fname="$(basename "$img")"
        if [ ! -f "$OUT_DIR/images/$fname" ]; then
            cp "$img" "$OUT_DIR/images/$fname"
            print_ok "이미지 복사: $fname"
        else
            print_ok "이미지 이미 존재 (스킵): $fname"
        fi
    done
else
    echo -e "  ${YELLOW}SKIP${NC} 공유 이미지 디렉토리 없음: $SHARED_IMAGES"
    echo "         images/ 에 Docker 이미지를 수동으로 배치하세요."
fi

# ---- Step 7: 체크섬 생성 ----
print_info "Step 6: 체크섬 생성"
(
    cd "$OUT_DIR"
    sha256sum docker-compose.yml setup.sh setup.ps1 README.md \
        images/*.tar.gz 2>/dev/null \
        data/*.json 2>/dev/null \
        > CHECKSUMS.sha256 || true
)
print_ok "CHECKSUMS.sha256 생성"

# ---- 완료 요약 ----
echo ""
echo "============================================================"
echo -e "  ${GREEN}패키지 생성 완료!${NC}"
echo ""
echo "  출력 경로: $OUT_DIR"
echo ""
ls -lh "$OUT_DIR"
echo ""
echo "  다음 단계:"
echo "    1. $OUT_DIR/data/ 에 프로젝트 JSON 확인"
echo "    2. $OUT_DIR/images/ 에 Docker 이미지 확인"
echo "    3. 패키지를 고객에게 전달"
echo "    4. 고객: ./setup.sh (Linux/macOS) 또는 .\\setup.ps1 (Windows)"
echo "============================================================"
