#!/bin/bash
# AI Drawing Analysis System - 복구 스크립트
# 백업으로부터 시스템 복구

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "🔄 시스템 복구 시작"
echo "============================================"
echo ""

# 백업 경로 확인
if [ -z "$1" ]; then
    echo -e "${RED}❌ 백업 경로를 지정해주세요.${NC}"
    echo ""
    echo "사용법: $0 <backup_path>"
    echo ""
    echo "예시:"
    echo "  $0 /home/uproot/ax/poc/backups/backup_20250114_153000"
    echo "  $0 /home/uproot/ax/poc/backups/backup_20250114_153000.tar.gz"
    echo ""
    exit 1
fi

BACKUP_PATH="$1"

# 백업 존재 확인
if [ ! -e "$BACKUP_PATH" ]; then
    echo -e "${RED}❌ 백업을 찾을 수 없습니다: $BACKUP_PATH${NC}"
    exit 1
fi

echo "백업 경로: $BACKUP_PATH"
echo ""

# 압축 파일인 경우 압축 해제
if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
    echo "1. 백업 압축 해제 중..."

    # 체크섬 검증
    if [ -f "${BACKUP_PATH}.sha256" ]; then
        echo "  체크섬 검증 중..."
        cd "$(dirname "$BACKUP_PATH")"
        if sha256sum -c "$(basename "${BACKUP_PATH}.sha256")"; then
            echo -e "  ${GREEN}✅ 체크섬 검증 완료${NC}"
        else
            echo -e "  ${RED}❌ 체크섬 검증 실패${NC}"
            read -p "  계속 진행하시겠습니까? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo -e "  ${YELLOW}⚠️  체크섬 파일이 없습니다${NC}"
    fi

    # 압축 해제
    EXTRACT_DIR="$(dirname "$BACKUP_PATH")/$(basename "$BACKUP_PATH" .tar.gz)"
    cd "$(dirname "$BACKUP_PATH")"
    tar -xzf "$(basename "$BACKUP_PATH")"
    BACKUP_DIR="$EXTRACT_DIR"
    echo -e "  ${GREEN}✅ 압축 해제 완료: $BACKUP_DIR${NC}"
else
    BACKUP_DIR="$BACKUP_PATH"
fi

echo ""

# 백업 정보 확인
if [ -f "${BACKUP_DIR}/backup_info.txt" ]; then
    echo "============================================"
    echo "📋 백업 정보"
    echo "============================================"
    cat "${BACKUP_DIR}/backup_info.txt"
    echo ""
fi

# 복구 확인
echo -e "${YELLOW}⚠️  WARNING: 현재 시스템 설정과 모델이 백업으로 교체됩니다!${NC}"
echo ""
read -p "복구를 진행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "복구가 취소되었습니다."
    exit 0
fi

echo ""
echo "============================================"
echo "복구 시작..."
echo "============================================"
echo ""

# Docker 컨테이너 중지
echo "1. Docker 컨테이너 중지 중..."
cd "$PROJECT_ROOT"
if docker-compose ps | grep -q "Up"; then
    docker-compose down || echo -e "${YELLOW}⚠️  일부 컨테이너 중지 실패${NC}"
    echo -e "${GREEN}✅ 컨테이너 중지 완료${NC}"
else
    echo "  ⏭️  실행 중인 컨테이너 없음"
fi

echo ""

# Docker 설정 복구
echo "2. Docker 설정 복구 중..."

if [ -f "${BACKUP_DIR}/docker-compose.yml" ]; then
    cp "${BACKUP_DIR}/docker-compose.yml" "${PROJECT_ROOT}/"
    echo "  ✅ docker-compose.yml"
fi

if [ -f "${BACKUP_DIR}/.env" ]; then
    # 기존 .env 백업
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        cp "${PROJECT_ROOT}/.env" "${PROJECT_ROOT}/.env.before_restore"
        echo "  📦 기존 .env를 .env.before_restore로 백업"
    fi

    cp "${BACKUP_DIR}/.env" "${PROJECT_ROOT}/"
    echo "  ✅ .env"
fi

echo ""

# 환경 설정 복구
echo "3. 환경 설정 복구 중..."

CONFIG_DIRS=(
    "monitoring/prometheus"
    "monitoring/grafana"
)

for config_dir in "${CONFIG_DIRS[@]}"; do
    if [ -d "${BACKUP_DIR}/${config_dir}" ]; then
        mkdir -p "${PROJECT_ROOT}/${config_dir}"
        cp -r "${BACKUP_DIR}/${config_dir}"/* "${PROJECT_ROOT}/${config_dir}/"
        echo "  ✅ $config_dir"
    fi
done

echo ""

# AI 모델 복구
echo "4. AI 모델 파일 복구 중... (시간이 걸릴 수 있습니다)"

if [ -d "${BACKUP_DIR}/models" ]; then
    for api_dir in "${BACKUP_DIR}/models"/*; do
        if [ -d "$api_dir" ]; then
            api_name=$(basename "$api_dir")

            # 대상 디렉토리 결정
            TARGET_DIR="${PROJECT_ROOT}/${api_name}/models"

            if [ -d "$TARGET_DIR" ]; then
                # 기존 모델 백업
                if [ "$(ls -A $TARGET_DIR 2>/dev/null)" ]; then
                    BACKUP_SUFFIX=$(date '+%Y%m%d_%H%M%S')
                    mkdir -p "${TARGET_DIR}.before_restore_${BACKUP_SUFFIX}"
                    mv "${TARGET_DIR}"/* "${TARGET_DIR}.before_restore_${BACKUP_SUFFIX}/" 2>/dev/null || true
                    echo "  📦 기존 $api_name 모델 백업: ${TARGET_DIR}.before_restore_${BACKUP_SUFFIX}"
                fi

                # 모델 복구
                cp "${api_dir}"/* "${TARGET_DIR}/"
                file_count=$(ls -1 "${TARGET_DIR}" | wc -l)
                echo "  ✅ $api_name ($file_count files)"
            else
                echo "  ⚠️  $TARGET_DIR not found, skipping"
            fi
        fi
    done
else
    echo "  ⏭️  백업에 모델 파일 없음"
fi

echo ""

# 메타데이터 복구
echo "5. 학습 메타데이터 복구 중..."

if [ -d "${BACKUP_DIR}/metadata" ]; then
    for metadata_file in "${BACKUP_DIR}/metadata"/*; do
        if [ -f "$metadata_file" ]; then
            filename=$(basename "$metadata_file")

            # 대상 경로 결정 (추정)
            if [[ "$filename" == *"edgnet"* ]]; then
                cp "$metadata_file" "${PROJECT_ROOT}/edgnet-api/models/"
            elif [[ "$filename" == *"skinmodel"* ]]; then
                cp "$metadata_file" "${PROJECT_ROOT}/skinmodel-api/models/"
            fi

            echo "  ✅ $filename"
        fi
    done
else
    echo "  ⏭️  백업에 메타데이터 없음"
fi

echo ""

# 로그 복구
echo "6. 로그 파일 복구 중..."

if [ -d "${BACKUP_DIR}/logs" ]; then
    mkdir -p "${PROJECT_ROOT}/logs"
    cp -r "${BACKUP_DIR}/logs"/* "${PROJECT_ROOT}/logs/" 2>/dev/null || true
    log_count=$(ls -1 "${PROJECT_ROOT}/logs" 2>/dev/null | wc -l)
    echo "  ✅ $log_count log files"
else
    echo "  ⏭️  백업에 로그 파일 없음"
fi

echo ""

# 업로드 파일 복구
echo "7. 업로드 파일 확인 중..."

if [ -d "${BACKUP_DIR}/uploads" ]; then
    upload_count=$(find "${BACKUP_DIR}/uploads" -type f 2>/dev/null | wc -l)
    echo "  백업된 업로드 파일: $upload_count 개"

    read -p "  업로드 파일도 복구하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "${PROJECT_ROOT}/uploads"
        cp -r "${BACKUP_DIR}/uploads"/* "${PROJECT_ROOT}/uploads/"
        echo "  ✅ 업로드 파일 복구 완료"
    else
        echo "  ⏭️  업로드 파일 복구 건너뜀"
    fi
else
    echo "  ⏭️  백업에 업로드 파일 없음"
fi

echo ""

# Docker 컨테이너 재시작
echo "8. Docker 컨테이너 재시작 중..."

cd "$PROJECT_ROOT"
docker-compose up -d || echo -e "${RED}❌ 일부 컨테이너 시작 실패${NC}"

echo "  컨테이너 초기화 대기 중 (30초)..."
sleep 30

echo ""

# 서비스 상태 확인
echo "9. 서비스 상태 확인 중..."

docker-compose ps

SERVICES=("web-ui" "gateway" "edocr2" "yolo" "edgnet" "skinmodel" "admin-dashboard")
RUNNING_COUNT=0

for service in "${SERVICES[@]}"; do
    if docker-compose ps | grep "$service" | grep -q "Up"; then
        echo -e "  ${GREEN}✅ $service: Running${NC}"
        ((RUNNING_COUNT++))
    else
        echo -e "  ${RED}❌ $service: NOT Running${NC}"
    fi
done

echo ""
echo "============================================"
echo "✅ 복구 완료!"
echo "============================================"
echo ""
echo "실행 중인 서비스: $RUNNING_COUNT / ${#SERVICES[@]}"
echo ""
echo "Web UI:          http://localhost:5173"
echo "Admin Dashboard: http://localhost:5173/admin"
echo ""
echo "============================================"
echo "📋 다음 단계"
echo "============================================"
echo ""
echo "1. 웹 UI에서 시스템 정상 작동 확인"
echo "2. 관리자 페이지에서 모델 상태 확인"
echo "3. 테스트 도면으로 분석 테스트"
echo ""
echo "문제가 있는 경우:"
echo "  - 로그 확인: docker-compose logs [service_name]"
echo "  - 상태 확인: bash scripts/health_check.sh"
echo "  - 서비스 재시작: docker-compose restart [service_name]"
echo ""

# 복구 로그 저장
RESTORE_LOG="${PROJECT_ROOT}/restore_$(date '+%Y%m%d_%H%M%S').log"
cat > "$RESTORE_LOG" <<EOF
AI Drawing Analysis System - Restore Log
=========================================

Restore Date: $(date '+%Y-%m-%d %H:%M:%S')
Backup Source: $BACKUP_PATH
Restore Location: $PROJECT_ROOT

Services Status:
----------------
Running: $RUNNING_COUNT / ${#SERVICES[@]}

$(docker-compose ps)

EOF

echo "복구 로그 저장: $RESTORE_LOG"
echo ""
