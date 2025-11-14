#!/bin/bash
# 개선 사항 적용 스크립트
# 이 스크립트는 모든 개선사항을 한번에 적용합니다.

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_step() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 현재 디렉토리 확인
if [ ! -d "/home/uproot/ax/poc" ]; then
    print_error "POC 디렉토리를 찾을 수 없습니다."
    exit 1
fi

cd /home/uproot/ax/poc

print_step "1. 사전 확인"

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    print_error "Python 3가 설치되어 있지 않습니다."
    exit 1
fi
print_success "Python 3 설치 확인됨"

# Docker 확인
if ! command -v docker &> /dev/null; then
    print_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi
print_success "Docker 설치 확인됨"

# Docker Compose 확인
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi
print_success "Docker Compose 설치 확인됨"

print_step "2. Common 모듈 의존성 설치"

if [ -f "common/requirements.txt" ]; then
    pip install -r common/requirements.txt
    print_success "Common 모듈 의존성 설치 완료"
else
    print_warning "common/requirements.txt를 찾을 수 없습니다."
fi

print_step "3. 환경 설정 파일 생성"

# .env 파일 생성 (존재하지 않는 경우)
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template .env
        print_success ".env 파일 생성됨"
        print_warning "⚠️  .env 파일을 편집하여 설정을 커스터마이징하세요!"
    else
        print_error ".env.template을 찾을 수 없습니다."
    fi
else
    print_warning ".env 파일이 이미 존재합니다. 건너뜁니다."
fi

# security_config.yaml 생성 (선택)
if [ ! -f "security_config.yaml" ]; then
    if [ -f "security_config.yaml.template" ]; then
        read -p "보안 설정 파일을 생성하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp security_config.yaml.template security_config.yaml
            print_success "security_config.yaml 생성됨"
            print_warning "⚠️  API 키를 생성하여 security_config.yaml에 추가하세요!"
            echo "API 키 생성 예시: openssl rand -hex 32"
        fi
    fi
fi

print_step "4. 기존 서비스 중지"

# 기존 서비스가 실행 중인지 확인
if docker-compose ps | grep -q "Up"; then
    read -p "기존 서비스를 중지하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down
        print_success "기존 서비스 중지됨"
    else
        print_warning "기존 서비스가 계속 실행됩니다."
    fi
fi

print_step "5. Enhanced 모드로 서비스 시작"

# Enhanced docker-compose 확인
if [ ! -f "docker-compose.enhanced.yml" ]; then
    print_error "docker-compose.enhanced.yml을 찾을 수 없습니다."
    exit 1
fi

read -p "Enhanced 모드로 서비스를 시작하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose -f docker-compose.enhanced.yml up -d
    print_success "Enhanced 모드로 서비스 시작됨"

    # 서비스 시작 대기
    print_success "서비스 시작 대기 중... (10초)"
    sleep 10
else
    print_warning "서비스 시작을 건너뜁니다."
    print_warning "수동 시작: docker-compose -f docker-compose.enhanced.yml up -d"
fi

print_step "6. Health Check"

# Health check 함수
check_health() {
    local service=$1
    local url=$2

    if curl -s -f "$url" > /dev/null; then
        print_success "$service: Healthy"
        return 0
    else
        print_error "$service: Unhealthy or Unreachable"
        return 1
    fi
}

# 각 서비스 확인
check_health "Gateway API" "http://localhost:8000/api/v1/health" || true
check_health "eDOCr2 v1" "http://localhost:5001/api/v1/health" || true
check_health "eDOCr2 v2" "http://localhost:5002/api/v2/health" || true
check_health "EDGNet" "http://localhost:5012/api/v1/health" || true
check_health "Skin Model" "http://localhost:5003/api/v1/health" || true
check_health "Prometheus" "http://localhost:9090/-/healthy" || true
check_health "Grafana" "http://localhost:3000/api/health" || true

print_step "7. 테스트 실행 (선택)"

read -p "통합 테스트를 실행하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "TODO/scripts/test_improvements.py" ]; then
        python3 TODO/scripts/test_improvements.py
        print_success "통합 테스트 완료"
    else
        print_warning "test_improvements.py를 찾을 수 없습니다."
    fi
fi

print_step "8. 완료!"

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}           개선 사항 적용 완료!${NC}"
echo -e "${GREEN}================================================================${NC}\n"

echo "다음 단계:"
echo "  1. Prometheus: http://localhost:9090"
echo "  2. Grafana: http://localhost:3000 (admin/admin)"
echo "  3. Web UI: http://localhost:5173"
echo ""
echo "추가 작업:"
echo "  - Grafana 대시보드 설정: TODO/STARTUP_GUIDE.md 참고"
echo "  - 데모 실행: python3 TODO/scripts/demo_full_system.py"
echo "  - 벤치마크: python3 TODO/scripts/benchmark_system.py"
echo ""
echo "문서:"
echo "  - 빠른 참조: cat TODO/QUICK_REFERENCE.md"
echo "  - 통합 가이드: cat TODO/INTEGRATION_GUIDE.md"
echo ""

print_success "모든 작업이 완료되었습니다!"
