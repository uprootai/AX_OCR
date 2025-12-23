#!/bin/bash
# Blueprint AI BOM - On-Premises Deployment Script
#
# 사용법:
#   ./scripts/deploy_onprem.sh [start|stop|restart|status|logs]
#
# 환경변수:
#   BACKEND_PORT - 백엔드 포트 (기본값: 5020)
#   FRONTEND_PORT - 프론트엔드 포트 (기본값: 3000)
#   YOLO_API_URL - YOLO API URL (선택)
#   EDOCR2_API_URL - eDOCr2 API URL (선택)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.onprem.yml"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되어 있지 않습니다."
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose가 설치되어 있지 않습니다."
        exit 1
    fi
}

compose_cmd() {
    if docker compose version &> /dev/null; then
        docker compose -f "$COMPOSE_FILE" "$@"
    else
        docker-compose -f "$COMPOSE_FILE" "$@"
    fi
}

start() {
    log_info "Blueprint AI BOM 시작 중..."
    compose_cmd up -d --build
    log_info "서비스가 시작되었습니다."
    log_info "Frontend: http://localhost:${FRONTEND_PORT:-3000}"
    log_info "Backend API: http://localhost:${BACKEND_PORT:-5020}"
    log_info "Health: http://localhost:${BACKEND_PORT:-5020}/health"
}

stop() {
    log_info "Blueprint AI BOM 중지 중..."
    compose_cmd down
    log_info "서비스가 중지되었습니다."
}

restart() {
    stop
    start
}

status() {
    log_info "컨테이너 상태:"
    compose_cmd ps

    echo ""
    log_info "Health Check:"
    if curl -sf "http://localhost:${BACKEND_PORT:-5020}/health" > /dev/null 2>&1; then
        echo -e "  Backend: ${GREEN}Healthy${NC}"
    else
        echo -e "  Backend: ${RED}Unhealthy${NC}"
    fi

    if curl -sf "http://localhost:${FRONTEND_PORT:-3000}" > /dev/null 2>&1; then
        echo -e "  Frontend: ${GREEN}Healthy${NC}"
    else
        echo -e "  Frontend: ${RED}Unhealthy${NC}"
    fi
}

logs() {
    compose_cmd logs -f
}

# 필수 디렉토리 생성
create_dirs() {
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/results"
    mkdir -p "$PROJECT_DIR/config"
}

# 메인
check_docker
create_dirs

case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Blueprint AI BOM - On-Premises Deployment"
        echo ""
        echo "사용법: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "명령어:"
        echo "  start   - 서비스 시작"
        echo "  stop    - 서비스 중지"
        echo "  restart - 서비스 재시작"
        echo "  status  - 서비스 상태 확인"
        echo "  logs    - 로그 확인"
        exit 1
        ;;
esac
