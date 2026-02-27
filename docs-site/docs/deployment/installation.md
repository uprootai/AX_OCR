---
sidebar_position: 1
sidebar_label: Installation
title: 시스템 설치 가이드
---

# AX 도면 분석 시스템 - 설치 가이드

> 온프레미스 납품용 설치 및 운영 매뉴얼
> 버전: 1.1.0

---

## 시스템 요구사항

### 최소 사양
- **OS**: Ubuntu 20.04 LTS / CentOS 8 / RHEL 8 이상
- **CPU**: 4 Core 이상
- **RAM**: 16GB 이상
- **디스크**: 100GB 이상 (SSD 권장)
- **네트워크**: 1Gbps 이상

### 권장 사양 (GPU 사용 시)
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 8 Core 이상 (Intel Xeon / AMD EPYC)
- **RAM**: 32GB 이상
- **GPU**: NVIDIA GPU (CUDA 11.8 이상 지원)
  - VRAM 8GB 이상 (RTX 3070 / A4000 이상)
- **디스크**: 200GB 이상 (NVMe SSD)
- **네트워크**: 10Gbps

### 소프트웨어 요구사항
- Docker 24.0 이상
- Docker Compose 2.20 이상
- (GPU 사용 시) NVIDIA Docker Runtime

---

## 사전 준비사항

### 1. Docker 설치

#### Ubuntu/Debian
```bash
# 기존 Docker 제거 (있는 경우)
sudo apt-get remove docker docker-engine docker.io containerd runc

# 필수 패키지 설치
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker GPG 키 추가
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 저장소 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 설치 확인
docker --version
docker compose version
```

#### CentOS/RHEL
```bash
# 기존 Docker 제거
sudo yum remove docker \
    docker-client \
    docker-client-latest \
    docker-common \
    docker-latest \
    docker-latest-logrotate \
    docker-logrotate \
    docker-engine

# Docker 저장소 설정
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# Docker 설치
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker 시작
sudo systemctl start docker
sudo systemctl enable docker

# 설치 확인
docker --version
docker compose version
```

### 2. NVIDIA Docker 설치 (GPU 사용 시)

```bash
# NVIDIA Driver 설치 확인
nvidia-smi

# NVIDIA Container Toolkit 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Docker 재시작
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 3. 방화벽 설정

```bash
# Ubuntu UFW
sudo ufw allow 5173/tcp  # Web UI
sudo ufw allow 8000/tcp  # Gateway API
sudo ufw allow 5002/tcp  # eDOCr2 API
sudo ufw allow 5003/tcp  # Skin Model API
sudo ufw allow 5005/tcp  # YOLO API
sudo ufw allow 5006/tcp  # PaddleOCR API
sudo ufw allow 5012/tcp  # EDGNet API

# CentOS/RHEL firewalld
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --permanent --add-port=5003/tcp
sudo firewall-cmd --permanent --add-port=5005/tcp
sudo firewall-cmd --permanent --add-port=5006/tcp
sudo firewall-cmd --permanent --add-port=5012/tcp
sudo firewall-cmd --reload
```

---

## 설치 절차

### 1. 시스템 파일 압축 해제

```bash
# 설치 디렉토리 생성
sudo mkdir -p /opt/ax-drawing-analysis
cd /opt/ax-drawing-analysis

# 압축 파일 해제 (납품 파일 경로에 따라 조정)
tar -xzf ax-drawing-analysis-v1.0.0.tar.gz

# 권한 설정
sudo chown -R $(whoami):$(whoami) /opt/ax-drawing-analysis
```

### 2. 디렉토리 구조 확인

```
/opt/ax-drawing-analysis/
├── docker-compose.yml          # Docker Compose 설정
├── .env.example                # 환경변수 템플릿
├── web-ui/                     # 웹 UI 소스
├── services/                   # 각 AI 모델 서비스
│   ├── gateway-api/
│   ├── yolo-api/
│   ├── edocr2-api/
│   ├── edgnet-api/
│   ├── paddleocr-api/
│   └── skinmodel-api/
├── models/                     # AI 모델 가중치
├── data/                       # 데이터 저장소
├── logs/                       # 로그 파일
└── docs/                       # 문서
```

### 3. 환경 설정 파일 생성

```bash
# 환경 변수 파일 복사
cp .env.example .env

# 에디터로 .env 파일 수정
vi .env
```

#### .env 파일 예시
```bash
# 기본 설정
COMPOSE_PROJECT_NAME=ax-drawing-analysis
NODE_ENV=production

# 포트 설정
WEB_UI_PORT=5173
GATEWAY_API_PORT=8000
YOLO_API_PORT=5005
EDOCR2_API_PORT=5002
EDGNET_API_PORT=5012
PADDLE_API_PORT=5006
SKINMODEL_API_PORT=5003

# GPU 설정 (true/false)
USE_GPU=true

# 메모리 제한
GATEWAY_MEMORY=2g
YOLO_MEMORY=4g
YOLO_GPU_MEMORY=4g
EDOCR2_MEMORY=4g
EDOCR2_GPU_MEMORY=6g
EDGNET_MEMORY=4g
EDGNET_GPU_MEMORY=4g
PADDLE_MEMORY=2g
SKINMODEL_MEMORY=2g

# 로그 레벨
LOG_LEVEL=info
```

---

## 초기 설정

### 1. 모델 파일 배치

```bash
# 모델 가중치 파일이 올바른 위치에 있는지 확인
ls -lh models/
# 출력 예시:
# yolo11_best.pt
# edocr2_v2.pth
# edgnet_weights.pth
```

### 2. 도커 이미지 빌드

```bash
cd /opt/ax-drawing-analysis

# 모든 서비스 이미지 빌드 (최초 1회, 약 10~20분 소요)
docker compose build

# 빌드 확인
docker images | grep ax-drawing
```

---

## 서비스 시작/중지

### 전체 서비스 시작

```bash
cd /opt/ax-drawing-analysis

# 백그라운드 모드로 시작
docker compose up -d

# 실시간 로그 확인
docker compose logs -f

# 특정 서비스 로그만 확인
docker compose logs -f web-ui
docker compose logs -f gateway-api
```

### 서비스 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker compose ps

# 헬스체크
curl http://localhost:8000/health
curl http://localhost:5005/health
```

### 서비스 중지

```bash
# 모든 서비스 중지 (컨테이너 제거)
docker compose down

# 컨테이너만 중지 (제거하지 않음)
docker compose stop

# 특정 서비스만 재시작
docker compose restart gateway-api
```

### 서비스 재시작

```bash
# 전체 재시작
docker compose restart

# 설정 변경 후 재시작
docker compose down
docker compose up -d
```

---

## 포트 설정 변경

### 방법 1: .env 파일 수정 (권장)

```bash
# .env 파일 편집
vi .env

# 포트 변경 예시
WEB_UI_PORT=8080  # 5173 -> 8080으로 변경

# 서비스 재시작
docker compose down
docker compose up -d
```

### 방법 2: docker-compose.yml 직접 수정

```yaml
# docker-compose.yml
services:
  web-ui:
    ports:
      - "8080:5173"  # 호스트:컨테이너
```

---

## GPU 설정

### GPU 사용 활성화

```bash
# .env 파일에서 GPU 설정
USE_GPU=true

# GPU 메모리 할당량 설정
YOLO_GPU_MEMORY=4g
EDOCR2_GPU_MEMORY=6g
EDGNET_GPU_MEMORY=4g
```

### GPU 사용 확인

```bash
# 컨테이너에서 GPU 인식 확인
docker exec -it yolo-api nvidia-smi

# GPU 사용률 모니터링
watch -n 1 nvidia-smi
```

### CPU 전용 모드로 변경

```bash
# .env 파일 수정
USE_GPU=false

# 서비스 재시작
docker compose down
docker compose up -d
```

---

## 백업 및 복원

### 설정 백업

```bash
# 설정 파일 백업
mkdir -p /opt/ax-backups/$(date +%Y%m%d)
cp .env /opt/ax-backups/$(date +%Y%m%d)/
cp -r data/ /opt/ax-backups/$(date +%Y%m%d)/

# 웹 UI 설정 백업 (브라우저 localStorage)
# Settings 페이지에서 "백업" 버튼 클릭 -> JSON 파일 다운로드
```

### 데이터베이스 백업 (향후 DB 추가 시)

```bash
# PostgreSQL 예시
docker exec postgres-db pg_dump -U axuser axdb > /opt/ax-backups/axdb_$(date +%Y%m%d).sql
```

### 복원

```bash
# 설정 파일 복원
cp /opt/ax-backups/20251113/.env .env
cp -r /opt/ax-backups/20251113/data/ ./

# 서비스 재시작
docker compose down
docker compose up -d
```

---

## 업그레이드

### 마이너 버전 업그레이드 (1.0.0 -> 1.1.0)

```bash
# 1. 현재 설정 백업
./scripts/backup.sh

# 2. 서비스 중지
docker compose down

# 3. 새 버전 압축 해제
tar -xzf ax-drawing-analysis-v1.1.0.tar.gz

# 4. 설정 파일 병합 (새로운 설정 항목 확인)
diff .env.example .env

# 5. 이미지 재빌드
docker compose build

# 6. 서비스 시작
docker compose up -d

# 7. 업그레이드 확인
curl http://localhost:8000/health | jq .version
```

### 메이저 버전 업그레이드 (1.x -> 2.x)

별도 업그레이드 가이드 참조 (docs/UPGRADE_GUIDE.md)

---

## 문제 해결

### 1. 서비스가 시작되지 않을 때

```bash
# 로그 확인
docker compose logs

# 특정 서비스 로그 상세 확인
docker compose logs --tail=100 gateway-api

# 컨테이너 상태 확인
docker compose ps
docker inspect <container_name>
```

### 2. 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8000
sudo netstat -tulpn | grep 8000

# 프로세스 종료 또는 .env에서 포트 변경
```

### 3. GPU 인식 안 됨

```bash
# NVIDIA Driver 확인
nvidia-smi

# Docker GPU 지원 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# nvidia-container-toolkit 재설치
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

### 4. 메모리 부족

```bash
# Docker 메모리 사용량 확인
docker stats

# .env에서 메모리 제한 조정
YOLO_MEMORY=2g  # 4g -> 2g로 감소
```

### 5. 웹 UI 접속 불가

```bash
# 웹 서버 로그 확인
docker compose logs web-ui

# 방화벽 확인
sudo ufw status
curl http://localhost:5173

# 브라우저 캐시 삭제 후 재시도
```

### 6. API 응답 느림

```bash
# GPU 사용률 확인
nvidia-smi

# CPU 사용률 확인
top

# 네트워크 대역폭 확인
iftop

# 로그 레벨 낮추기 (.env)
LOG_LEVEL=warn
```
