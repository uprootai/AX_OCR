#!/bin/bash
# AI Drawing Analysis System - 자동 설치 스크립트
# 온프레미스 환경 설치 자동화

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_LOG="${PROJECT_ROOT}/install.log"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로깅 함수
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$INSTALL_LOG"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$INSTALL_LOG"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$INSTALL_LOG"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$INSTALL_LOG"
}

# 에러 핸들러
error_exit() {
    log_error "설치 실패: $1"
    log_error "로그 파일을 확인하세요: $INSTALL_LOG"
    exit 1
}

# 사용자 확인
confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "사용자가 취소했습니다."
        exit 0
    fi
}

echo "============================================"
echo "🚀 AI Drawing Analysis System"
echo "   온프레미스 설치 스크립트"
echo "============================================"
echo ""

# Root 권한 확인
if [[ $EUID -ne 0 ]]; then
   log_error "이 스크립트는 root 권한이 필요합니다."
   echo "sudo $0 실행하세요."
   exit 1
fi

log "설치 로그: $INSTALL_LOG"
echo "" | tee -a "$INSTALL_LOG"

# 1. 시스템 요구사항 검증
log "1단계: 시스템 요구사항 검증"
echo "----------------------------------------"

if [ -f "${SCRIPT_DIR}/check_system.sh" ]; then
    bash "${SCRIPT_DIR}/check_system.sh" || {
        log_error "시스템 요구사항을 충족하지 못했습니다."
        confirm "계속 진행하시겠습니까?"
    }
    log_success "시스템 요구사항 검증 완료"
else
    log_warn "check_system.sh를 찾을 수 없습니다. 검증을 건너뜁니다."
fi
echo ""

# 2. Docker 이미지 로드 (오프라인 설치 시)
log "2단계: Docker 이미지 로드"
echo "----------------------------------------"

OFFLINE_PACKAGE="${PROJECT_ROOT}/offline_package/docker_images.tar.gz"

if [ -f "$OFFLINE_PACKAGE" ]; then
    log "오프라인 패키지 발견: $OFFLINE_PACKAGE"

    # 체크섬 검증
    if [ -f "${OFFLINE_PACKAGE%.tar.gz}.sha256" ]; then
        log "체크섬 검증 중..."
        cd "$(dirname "$OFFLINE_PACKAGE")"
        sha256sum -c "$(basename "${OFFLINE_PACKAGE%.tar.gz}.sha256")" || error_exit "체크섬 검증 실패"
        log_success "체크섬 검증 완료"
    fi

    # 압축 해제
    log "Docker 이미지 압축 해제 중..."
    cd "$(dirname "$OFFLINE_PACKAGE")"
    tar -xzf "$(basename "$OFFLINE_PACKAGE")" || error_exit "압축 해제 실패"

    # Docker 이미지 로드
    log "Docker 이미지 로드 중... (시간이 걸릴 수 있습니다)"
    for tar_file in *.tar; do
        if [ -f "$tar_file" ]; then
            log "  Loading: $tar_file"
            docker load -i "$tar_file" || log_warn "Failed to load: $tar_file"
        fi
    done

    # 정리
    rm -f *.tar
    log_success "Docker 이미지 로드 완료"
else
    log_warn "오프라인 패키지를 찾을 수 없습니다."
    log "Docker Hub에서 이미지를 pull합니다..."

    # docker-compose.yml 확인
    if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
        cd "$PROJECT_ROOT"
        docker-compose pull || log_warn "일부 이미지 pull 실패"
    else
        log_warn "docker-compose.yml을 찾을 수 없습니다."
    fi
fi
echo ""

# 3. 디렉토리 구조 생성
log "3단계: 디렉토리 구조 생성"
echo "----------------------------------------"

REQUIRED_DIRS=(
    "${PROJECT_ROOT}/data"
    "${PROJECT_ROOT}/logs"
    "${PROJECT_ROOT}/models"
    "${PROJECT_ROOT}/uploads"
    "${PROJECT_ROOT}/backups"
    "${PROJECT_ROOT}/monitoring/prometheus"
    "${PROJECT_ROOT}/monitoring/grafana"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log "  Created: $dir"
    fi
done

log_success "디렉토리 구조 생성 완료"
echo ""

# 4. 환경 변수 설정
log "4단계: 환경 변수 설정"
echo "----------------------------------------"

ENV_FILE="${PROJECT_ROOT}/.env"

if [ ! -f "$ENV_FILE" ]; then
    log "환경 변수 파일 생성 중..."
    cat > "$ENV_FILE" <<EOF
# AI Drawing Analysis System - Environment Variables

# System
PROJECT_ROOT=${PROJECT_ROOT}
INSTALL_DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Network
WEB_UI_PORT=5173
GATEWAY_PORT=8000
ADMIN_DASHBOARD_PORT=8007

# API Ports
EDOCR2_PORT=8001
YOLO_PORT=8002
EDGNET_PORT=8003
SKINMODEL_PORT=8004
VL_PORT=8005
PADDLEOCR_PORT=8006

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Security (CHANGE THESE IN PRODUCTION!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme123
JWT_SECRET=$(openssl rand -base64 32)

# Database (optional)
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=drawing_analysis
# DB_USER=dbuser
# DB_PASSWORD=dbpass

# External APIs (set to 'disabled' for on-premise)
VL_MODE=disabled
OPENAI_API_KEY=disabled
ANTHROPIC_API_KEY=disabled

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

EOF
    log_success "환경 변수 파일 생성 완료: $ENV_FILE"
    log_warn "보안을 위해 ADMIN_PASSWORD와 JWT_SECRET을 변경하세요!"
else
    log "환경 변수 파일이 이미 존재합니다: $ENV_FILE"
fi
echo ""

# 5. Docker Compose 설정 확인
log "5단계: Docker Compose 설정 확인"
echo "----------------------------------------"

if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
    cd "$PROJECT_ROOT"
    docker-compose config > /dev/null || error_exit "docker-compose.yml 설정 오류"
    log_success "docker-compose.yml 검증 완료"
else
    error_exit "docker-compose.yml을 찾을 수 없습니다."
fi
echo ""

# 6. 모델 파일 확인
log "6단계: AI 모델 파일 확인"
echo "----------------------------------------"

MODEL_DIRS=(
    "${PROJECT_ROOT}/edocr2-api/models"
    "${PROJECT_ROOT}/yolo-api/models"
    "${PROJECT_ROOT}/edgnet-api/models"
    "${PROJECT_ROOT}/skinmodel-api/models"
    "${PROJECT_ROOT}/vl-api/models"
    "${PROJECT_ROOT}/paddleocr-api/models"
)

for model_dir in "${MODEL_DIRS[@]}"; do
    if [ -d "$model_dir" ]; then
        model_count=$(find "$model_dir" -type f \( -name "*.pth" -o -name "*.pt" -o -name "*.pkl" -o -name "*.h5" \) 2>/dev/null | wc -l)
        if [ "$model_count" -gt 0 ]; then
            log "  ✅ $model_dir: $model_count model(s) found"
        else
            log_warn "  ⚠️  $model_dir: No models found"
        fi
    else
        log_warn "  ⚠️  $model_dir: Directory not found"
    fi
done

log_success "모델 파일 확인 완료"
echo ""

# 7. Prometheus & Grafana 설정
log "7단계: Monitoring 설정 (Prometheus & Grafana)"
echo "----------------------------------------"

if [ -f "${PROJECT_ROOT}/monitoring/prometheus/prometheus.yml" ]; then
    log_success "Prometheus 설정 파일 확인 완료"
else
    log_warn "Prometheus 설정 파일이 없습니다. 기본 설정을 생성합니다."
    # prometheus.yml 생성은 별도 스크립트에서 처리
fi

if [ -d "${PROJECT_ROOT}/monitoring/grafana/dashboards" ]; then
    dashboard_count=$(find "${PROJECT_ROOT}/monitoring/grafana/dashboards" -name "*.json" 2>/dev/null | wc -l)
    log "  Grafana 대시보드: $dashboard_count 개 발견"
else
    log_warn "Grafana 대시보드 디렉토리가 없습니다."
fi
echo ""

# 8. 컨테이너 실행
log "8단계: Docker 컨테이너 실행"
echo "----------------------------------------"

cd "$PROJECT_ROOT"

# 기존 컨테이너 정리 (선택)
if docker ps -a | grep -q "poc_"; then
    log_warn "기존 컨테이너가 실행 중입니다."
    confirm "기존 컨테이너를 중지하고 재시작하시겠습니까?"

    log "기존 컨테이너 중지 및 제거 중..."
    docker-compose down || true
fi

# 컨테이너 실행
log "Docker Compose로 모든 서비스 시작 중..."
docker-compose up -d || error_exit "Docker Compose 실행 실패"

log_success "Docker 컨테이너 실행 완료"
echo ""

# 9. 서비스 상태 확인
log "9단계: 서비스 상태 확인"
echo "----------------------------------------"

log "컨테이너 초기화 대기 중 (30초)..."
sleep 30

log "서비스 상태 확인 중..."
docker-compose ps

# Health check
SERVICES=("web-ui" "gateway" "edocr2" "yolo" "edgnet" "skinmodel" "admin-dashboard")
FAILED_SERVICES=()

for service in "${SERVICES[@]}"; do
    if docker-compose ps | grep "$service" | grep -q "Up"; then
        log_success "  $service: Running"
    else
        log_error "  $service: NOT Running"
        FAILED_SERVICES+=("$service")
    fi
done

if [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    log_success "모든 서비스가 정상 실행 중입니다!"
else
    log_error "일부 서비스가 실행되지 않았습니다: ${FAILED_SERVICES[*]}"
    log_warn "로그를 확인하세요: docker-compose logs [service_name]"
fi
echo ""

# 10. 설치 완료 및 정보 출력
log "10단계: 설치 완료"
echo "============================================"
echo ""
log_success "🎉 AI Drawing Analysis System 설치 완료!"
echo ""
echo "============================================"
echo "📋 시스템 접속 정보"
echo "============================================"
echo ""
echo "Web UI:            http://localhost:5173"
echo "Admin Dashboard:   http://localhost:5173/admin"
echo "API Gateway:       http://localhost:8000"
echo "Prometheus:        http://localhost:9090 (설정 시)"
echo "Grafana:           http://localhost:3000 (설정 시)"
echo ""
echo "============================================"
echo "🔐 기본 관리자 계정"
echo "============================================"
echo ""
echo "Username: admin"
echo "Password: changeme123"
echo ""
echo "⚠️  보안을 위해 반드시 비밀번호를 변경하세요!"
echo ""
echo "============================================"
echo "📖 다음 단계"
echo "============================================"
echo ""
echo "1. 웹 브라우저에서 http://localhost:5173 접속"
echo "2. 관리자 페이지에서 모델 상태 확인"
echo "3. 테스트 도면 업로드 및 분석 테스트"
echo "4. 필요 시 모델 재학습 수행"
echo ""
echo "============================================"
echo "🛠️  유용한 명령어"
echo "============================================"
echo ""
echo "서비스 상태 확인:    docker-compose ps"
echo "로그 확인:          docker-compose logs -f [service_name]"
echo "서비스 재시작:       docker-compose restart [service_name]"
echo "전체 중지:          docker-compose down"
echo "백업:               bash scripts/backup.sh"
echo "상태 체크:          bash scripts/health_check.sh"
echo ""
echo "============================================"
echo ""

log "설치 로그 저장 위치: $INSTALL_LOG"
log_success "설치 프로세스 완료!"
