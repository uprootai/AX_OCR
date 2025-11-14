#!/bin/bash
# AI Drawing Analysis System - 백업 스크립트
# 모델, 데이터, 설정 파일 백업

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_ROOT="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR="${BACKUP_ROOT}/backup_${TIMESTAMP}"

echo "============================================"
echo "💾 시스템 백업 시작"
echo "============================================"
echo ""
echo "백업 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "백업 위치: $BACKUP_DIR"
echo ""

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# 1. Docker 설정 백업
echo "1. Docker 설정 백업 중..."
if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    cp "${PROJECT_ROOT}/docker-compose.yml" "${BACKUP_DIR}/"
    echo "  ✅ docker-compose.yml"
fi

if [ -f "${PROJECT_ROOT}/.env" ]; then
    cp "${PROJECT_ROOT}/.env" "${BACKUP_DIR}/"
    echo "  ✅ .env"
fi

# 2. 환경 설정 파일 백업
echo ""
echo "2. 환경 설정 파일 백업 중..."
CONFIG_DIRS=(
    "monitoring/prometheus"
    "monitoring/grafana"
)

for config_dir in "${CONFIG_DIRS[@]}"; do
    if [ -d "${PROJECT_ROOT}/${config_dir}" ]; then
        mkdir -p "${BACKUP_DIR}/${config_dir}"
        cp -r "${PROJECT_ROOT}/${config_dir}"/* "${BACKUP_DIR}/${config_dir}/" 2>/dev/null || true
        echo "  ✅ $config_dir"
    fi
done

# 3. AI 모델 파일 백업
echo ""
echo "3. AI 모델 파일 백업 중... (시간이 걸릴 수 있습니다)"

MODEL_DIRS=(
    "edocr2-api/models"
    "yolo-api/models"
    "edgnet-api/models"
    "skinmodel-api/models"
    "vl-api/models"
    "paddleocr-api/models"
)

mkdir -p "${BACKUP_DIR}/models"

for model_dir in "${MODEL_DIRS[@]}"; do
    if [ -d "${PROJECT_ROOT}/${model_dir}" ]; then
        api_name=$(echo "$model_dir" | cut -d'/' -f1)
        mkdir -p "${BACKUP_DIR}/models/${api_name}"

        # .pth, .pt, .pkl, .h5 파일만 백업
        find "${PROJECT_ROOT}/${model_dir}" -type f \( -name "*.pth" -o -name "*.pt" -o -name "*.pkl" -o -name "*.h5" -o -name "*.json" \) \
            -exec cp {} "${BACKUP_DIR}/models/${api_name}/" \; 2>/dev/null || true

        file_count=$(find "${BACKUP_DIR}/models/${api_name}" -type f 2>/dev/null | wc -l)
        if [ "$file_count" -gt 0 ]; then
            echo "  ✅ $model_dir ($file_count files)"
        fi
    fi
done

# 4. 학습 데이터 메타데이터 백업
echo ""
echo "4. 학습 데이터 메타데이터 백업 중..."

METADATA_FILES=(
    "edgnet-api/models/training_metadata.json"
    "skinmodel-api/models/training_history.json"
)

mkdir -p "${BACKUP_DIR}/metadata"

for metadata_file in "${METADATA_FILES[@]}"; do
    if [ -f "${PROJECT_ROOT}/${metadata_file}" ]; then
        cp "${PROJECT_ROOT}/${metadata_file}" "${BACKUP_DIR}/metadata/"
        echo "  ✅ $(basename $metadata_file)"
    fi
done

# 5. 로그 백업 (최근 7일)
echo ""
echo "5. 로그 파일 백업 중 (최근 7일)..."

if [ -d "${PROJECT_ROOT}/logs" ]; then
    mkdir -p "${BACKUP_DIR}/logs"
    find "${PROJECT_ROOT}/logs" -type f -mtime -7 -exec cp {} "${BACKUP_DIR}/logs/" \; 2>/dev/null || true
    log_count=$(find "${BACKUP_DIR}/logs" -type f 2>/dev/null | wc -l)
    echo "  ✅ $log_count log files"
fi

# 6. 업로드된 파일 백업 (선택적)
echo ""
echo "6. 업로드 파일 확인 중..."

if [ -d "${PROJECT_ROOT}/uploads" ]; then
    upload_size=$(du -sh "${PROJECT_ROOT}/uploads" 2>/dev/null | cut -f1)
    echo "  업로드 디렉토리 크기: $upload_size"

    read -p "  업로드 파일도 백업하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "${BACKUP_DIR}/uploads"
        cp -r "${PROJECT_ROOT}/uploads"/* "${BACKUP_DIR}/uploads/" 2>/dev/null || true
        echo "  ✅ 업로드 파일 백업 완료"
    else
        echo "  ⏭️  업로드 파일 백업 건너뜀"
    fi
fi

# 7. 백업 정보 파일 생성
echo ""
echo "7. 백업 정보 파일 생성 중..."

cat > "${BACKUP_DIR}/backup_info.txt" <<EOF
AI Drawing Analysis System - Backup Information
================================================

Backup Date: $(date '+%Y-%m-%d %H:%M:%S')
Backup Location: $BACKUP_DIR
Hostname: $(hostname)
System: $(uname -a)

Backup Contents:
----------------
✅ Docker configurations (docker-compose.yml, .env)
✅ Monitoring configurations (Prometheus, Grafana)
✅ AI model files
✅ Training metadata
✅ Log files (last 7 days)

Model Backup Summary:
---------------------
$(find "${BACKUP_DIR}/models" -type f -name "*.pth" -o -name "*.pt" -o -name "*.pkl" -o -name "*.h5" 2>/dev/null | wc -l) model files

Docker Container Status at Backup Time:
----------------------------------------
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not running")

Restore Instructions:
---------------------
1. Extract backup to project root
2. Run: bash scripts/restore.sh $BACKUP_DIR

EOF

# 8. 압축 (선택)
echo ""
read -p "백업을 압축하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "백업 압축 중... (시간이 걸릴 수 있습니다)"
    cd "$BACKUP_ROOT"
    tar -czf "backup_${TIMESTAMP}.tar.gz" "backup_${TIMESTAMP}"

    # 체크섬 생성
    sha256sum "backup_${TIMESTAMP}.tar.gz" > "backup_${TIMESTAMP}.tar.gz.sha256"

    # 원본 디렉토리 삭제
    rm -rf "backup_${TIMESTAMP}"

    echo "  ✅ 압축 완료: backup_${TIMESTAMP}.tar.gz"
    echo "  ✅ 체크섬: backup_${TIMESTAMP}.tar.gz.sha256"

    BACKUP_FILE="${BACKUP_ROOT}/backup_${TIMESTAMP}.tar.gz"
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
else
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
fi

# 9. 이전 백업 정리 (30일 이상 오래된 백업 삭제)
echo ""
echo "9. 이전 백업 정리 중..."

OLD_BACKUPS=$(find "$BACKUP_ROOT" -name "backup_*" -mtime +30 2>/dev/null)
if [ -n "$OLD_BACKUPS" ]; then
    echo "  30일 이상 오래된 백업 발견:"
    echo "$OLD_BACKUPS"

    read -p "  삭제하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        find "$BACKUP_ROOT" -name "backup_*" -mtime +30 -delete
        echo "  ✅ 이전 백업 삭제 완료"
    fi
else
    echo "  ⏭️  삭제할 이전 백업 없음"
fi

# 최종 결과
echo ""
echo "============================================"
echo "✅ 백업 완료!"
echo "============================================"
echo ""
echo "백업 위치: ${BACKUP_DIR:-$BACKUP_FILE}"
echo "백업 크기: $BACKUP_SIZE"
echo ""
echo "백업 정보:"
cat "${BACKUP_DIR}/backup_info.txt" 2>/dev/null || cat <(tar -xzOf "${BACKUP_FILE}" backup_${TIMESTAMP}/backup_info.txt 2>/dev/null)
echo ""
echo "복구 방법:"
echo "  bash scripts/restore.sh $BACKUP_DIR"
echo ""
