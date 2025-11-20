#!/bin/bash
# 시스템 요구사항 검증 스크립트
# AI Drawing Analysis System 설치 전 사전 점검

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "🔍 시스템 요구사항 검증"
echo "============================================"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# 검증 함수
check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS_COUNT++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN_COUNT++))
}

# 1. OS 검증
echo "1. Operating System"
echo "----------------------------------------"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"

    if [[ "$ID" == "ubuntu" ]] && [[ "$VERSION_ID" == "20.04" || "$VERSION_ID" == "22.04" ]]; then
        check_pass "Ubuntu 20.04/22.04 detected"
    elif [[ "$ID" == "centos" || "$ID" == "rhel" ]]; then
        check_pass "CentOS/RHEL detected"
    else
        check_warn "OS not officially tested: $NAME $VERSION"
    fi
else
    check_fail "Cannot determine OS version"
fi
echo ""

# 2. CPU 검증
echo "2. CPU"
echo "----------------------------------------"
CPU_CORES=$(nproc)
echo "CPU Cores: $CPU_CORES"

if [ "$CPU_CORES" -ge 8 ]; then
    check_pass "CPU cores >= 8 (recommended)"
elif [ "$CPU_CORES" -ge 4 ]; then
    check_warn "CPU cores: $CPU_CORES (minimum 4, recommended 8+)"
else
    check_fail "CPU cores: $CPU_CORES (minimum required: 4)"
fi
echo ""

# 3. Memory 검증
echo "3. Memory"
echo "----------------------------------------"
TOTAL_MEM_GB=$(free -g | awk '/^Mem:/{print $2}')
echo "Total Memory: ${TOTAL_MEM_GB}GB"

if [ "$TOTAL_MEM_GB" -ge 16 ]; then
    check_pass "Memory >= 16GB (recommended)"
elif [ "$TOTAL_MEM_GB" -ge 8 ]; then
    check_warn "Memory: ${TOTAL_MEM_GB}GB (minimum 8GB, recommended 16GB+)"
else
    check_fail "Memory: ${TOTAL_MEM_GB}GB (minimum required: 8GB)"
fi
echo ""

# 4. Disk 공간 검증
echo "4. Disk Space"
echo "----------------------------------------"
DISK_AVAIL_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
echo "Available Disk Space: ${DISK_AVAIL_GB}GB"

if [ "$DISK_AVAIL_GB" -ge 100 ]; then
    check_pass "Disk space >= 100GB (recommended)"
elif [ "$DISK_AVAIL_GB" -ge 50 ]; then
    check_warn "Disk space: ${DISK_AVAIL_GB}GB (minimum 50GB, recommended 100GB+)"
else
    check_fail "Disk space: ${DISK_AVAIL_GB}GB (minimum required: 50GB)"
fi
echo ""

# 5. Docker 검증
echo "5. Docker"
echo "----------------------------------------"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "Docker Version: $DOCKER_VERSION"

    # Docker 서비스 실행 확인
    if systemctl is-active --quiet docker; then
        check_pass "Docker is installed and running"
    else
        check_fail "Docker is installed but not running"
    fi

    # Docker Compose 확인
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
        echo "Docker Compose Version: $COMPOSE_VERSION"
        check_pass "Docker Compose is installed"
    else
        check_fail "Docker Compose not found (required)"
    fi
else
    check_fail "Docker not found (required)"
fi
echo ""

# 6. GPU 검증 (선택사항)
echo "6. GPU (Optional but Recommended)"
echo "----------------------------------------"
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    GPU_MEM_GB=$((GPU_MEM / 1024))

    echo "GPU: $GPU_NAME"
    echo "GPU Memory: ${GPU_MEM_GB}GB"

    if [ "$GPU_MEM_GB" -ge 6 ]; then
        check_pass "GPU memory >= 6GB (recommended for training)"
    elif [ "$GPU_MEM_GB" -ge 4 ]; then
        check_warn "GPU memory: ${GPU_MEM_GB}GB (minimum 4GB, recommended 6GB+)"
    else
        check_warn "GPU memory: ${GPU_MEM_GB}GB (too small for training)"
    fi

    # CUDA 확인
    if command -v nvcc &> /dev/null; then
        CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | sed 's/,//')
        echo "CUDA Version: $CUDA_VERSION"
        check_pass "CUDA toolkit installed"
    else
        check_warn "CUDA toolkit not found (may affect GPU performance)"
    fi
else
    check_warn "NVIDIA GPU not detected (CPU-only mode, slower training)"
fi
echo ""

# 7. Network 포트 검증
echo "7. Network Ports"
echo "----------------------------------------"
REQUIRED_PORTS=(5173 8000 8001 8002 8003 8004 8005 8006 8007 9090 3000)
PORT_CONFLICTS=()

for port in "${REQUIRED_PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
        PORT_CONFLICTS+=($port)
    fi
done

if [ ${#PORT_CONFLICTS[@]} -eq 0 ]; then
    check_pass "All required ports are available"
else
    check_warn "Port conflicts detected: ${PORT_CONFLICTS[*]}"
    echo "       Required ports: ${REQUIRED_PORTS[*]}"
fi
echo ""

# 8. Python 검증
echo "8. Python (for scripts)"
echo "----------------------------------------"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "Python Version: $PYTHON_VERSION"

    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        check_pass "Python >= 3.8 (recommended 3.11)"
    else
        check_warn "Python $PYTHON_VERSION (recommended 3.11+)"
    fi
else
    check_fail "Python3 not found (required for management scripts)"
fi
echo ""

# 9. 방화벽 확인
echo "9. Firewall"
echo "----------------------------------------"
if systemctl is-active --quiet firewalld; then
    check_warn "firewalld is active (may need port configuration)"
    echo "       Run: sudo firewall-cmd --add-port={5173,8000-8007,9090,3000}/tcp --permanent"
elif systemctl is-active --quiet ufw; then
    check_warn "ufw is active (may need port configuration)"
    echo "       Run: sudo ufw allow 5173,8000:8007,9090,3000/tcp"
else
    check_pass "No active firewall detected"
fi
echo ""

# 10. SELinux 확인
echo "10. SELinux"
echo "----------------------------------------"
if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce)
    echo "SELinux Status: $SELINUX_STATUS"

    if [ "$SELINUX_STATUS" == "Enforcing" ]; then
        check_warn "SELinux is Enforcing (may require policy adjustments)"
    else
        check_pass "SELinux is $SELINUX_STATUS"
    fi
else
    check_pass "SELinux not installed"
fi
echo ""

# 최종 결과
echo "============================================"
echo "📊 검증 결과 요약"
echo "============================================"
echo -e "${GREEN}PASS: $PASS_COUNT${NC}"
echo -e "${YELLOW}WARN: $WARN_COUNT${NC}"
echo -e "${RED}FAIL: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ 시스템이 설치 요구사항을 충족합니다!${NC}"
    exit 0
elif [ $FAIL_COUNT -le 2 ]; then
    echo -e "${YELLOW}⚠️  일부 요구사항을 충족하지 못했습니다.${NC}"
    echo "   설치를 계속하려면 FAIL 항목을 해결하세요."
    exit 1
else
    echo -e "${RED}❌ 시스템이 최소 요구사항을 충족하지 못합니다.${NC}"
    echo "   설치 전에 FAIL 항목을 모두 해결하세요."
    exit 2
fi
