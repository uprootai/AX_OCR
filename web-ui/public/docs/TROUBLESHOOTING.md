# AX 도면 분석 시스템 - 트러블슈팅 가이드

> 문제 해결 매뉴얼
> **버전**: 2.0.0
> **최종 수정**: 2026-01-17

---

## 목차

1. [시스템 시작 문제](#1-시스템-시작-문제)
2. [성능 문제](#2-성능-문제)
3. [GPU 관련 문제](#3-gpu-관련-문제)
4. [네트워크 문제](#4-네트워크-문제)
5. [메모리 문제](#5-메모리-문제)
6. [로그 수집 방법](#6-로그-수집-방법)
7. [FAQ](#7-faq)

---

## API 포트 참조

| 서비스 | 포트 | 헬스체크 엔드포인트 |
|--------|------|---------------------|
| Gateway | 8000 | `/health` |
| YOLO | 5005 | `/health` |
| eDOCr2 | 5002 | `/api/v2/health` |
| SkinModel | 5003 | `/health` |
| VL | 5004 | `/health` |
| PaddleOCR | 5006 | `/health` |
| Knowledge | 5007 | `/health` |
| Tesseract | 5008 | `/health` |
| TrOCR | 5009 | `/health` |
| ESRGAN | 5010 | `/health` |
| OCR Ensemble | 5011 | `/health` |
| EDGNet | 5012 | `/health` |
| Surya OCR | 5013 | `/health` |
| DocTR | 5014 | `/health` |
| EasyOCR | 5015 | `/health` |
| Line Detector | 5016 | `/health` |
| PID Analyzer | 5018 | `/health` |
| Design Checker | 5019 | `/health` |
| Blueprint AI BOM | 5020 | `/health` |

---

## 1. 시스템 시작 문제

### 문제 1.1: `docker compose up` 실패

**증상:**
```bash
Error response from daemon: driver failed programming external connectivity
```

**원인:** 포트가 이미 사용 중

**해결:**
```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8000
sudo lsof -i :5005

# 프로세스 종료
sudo kill -9 <PID>

# 또는 .env에서 포트 변경 후 재시작
docker compose down
docker compose up -d
```

---

### 문제 1.2: 컨테이너 계속 재시작

**증상:**
```bash
$ docker compose ps
NAME         STATUS
yolo-api     Restarting (1) 5 seconds ago
```

**원인:** 메모리 부족, 모델 파일 누락

**해결:**
```bash
# 로그 확인
docker compose logs yolo-api

# 메모리 부족 시 .env 수정
YOLO_MEMORY=4g

# 모델 파일 확인
ls -lh models/yolo-api/models/
```

---

### 문제 1.3: Docker 데몬 연결 실패

**증상:**
```bash
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**해결:**
```bash
# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 권한 문제 시
sudo usermod -aG docker $USER
newgrp docker
```

---

## 2. 성능 문제

### 문제 2.1: API 응답 시간 느림 (>10초)

**원인:** CPU 모드 사용, GPU 메모리 부족

**해결:**
```bash
# GPU 사용 확인
docker exec yolo-api nvidia-smi

# GPU 미인식 시 .env 확인
USE_GPU=true

# 이미지 크기 조정 (Settings 페이지)
# YOLO imgsz: 1920 → 1280 (성능 우선)

# 서비스 재시작
docker compose restart yolo-api
```

---

### 문제 2.2: 웹 UI 로딩 느림

**원인:** 번들 파일 크기, 네트워크

**해결:**
```bash
# 브라우저 캐시 확인 (F12 → Network)
# 프로덕션 빌드 확인
docker compose exec web-ui ls -lh dist/
```

---

## 3. GPU 관련 문제

### 문제 3.1: GPU 인식 안 됨

**해결:**
```bash
# 호스트에서 GPU 확인
nvidia-smi

# NVIDIA Driver 미설치 시
sudo apt-get install nvidia-driver-535
sudo reboot

# nvidia-container-toolkit 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

### 문제 3.2: CUDA Out of Memory

**증상:**
```bash
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**해결:**
```bash
# GPU 메모리 사용량 확인
nvidia-smi

# 불필요한 서비스 중지
docker compose stop edgnet-api easyocr-api

# 입력 이미지 크기 감소
# YOLO imgsz: 1280 → 640

# GPU 메모리 할당량 조정 (.env)
YOLO_GPU_MEMORY=3g
EDOCR2_GPU_MEMORY=4g
```

---

## 4. 네트워크 문제

### 문제 4.1: 외부에서 웹 UI 접속 불가

**해결:**
```bash
# 방화벽 상태 확인
sudo ufw status

# 포트 열기 (Ubuntu)
sudo ufw allow 5173/tcp
sudo ufw allow 8000/tcp

# 포트 열기 (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5173/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

### 문제 4.2: API 간 통신 실패

**증상:**
```bash
Gateway API → YOLO API: Connection refused
```

**해결:**
```bash
# 컨테이너 네트워크 확인
docker network ls
docker network inspect ax-drawing-analysis_default

# 컨테이너 간 ping 테스트
docker exec gateway-api ping yolo-api

# 재시작
docker compose down
docker compose up -d

# 헬스체크
curl http://localhost:8000/health
curl http://localhost:5005/health
```

---

## 5. 메모리 문제

### 문제 5.1: "Cannot allocate memory" 오류

**해결:**
```bash
# 시스템 메모리 확인
free -h

# Docker 메모리 사용량 확인
docker stats

# 불필요한 컨테이너 정리
docker container prune
docker image prune -a

# 메모리 제한 조정 (.env)
YOLO_MEMORY=2g
EDOCR2_MEMORY=2g

# 스왑 메모리 설정 (임시)
sudo dd if=/dev/zero of=/swapfile bs=1G count=8
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 6. 로그 수집 방법

### 전체 로그 수집 스크립트

```bash
#!/bin/bash
# collect_logs.sh

BACKUP_DIR="/tmp/ax-logs-$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Docker 로그
docker compose logs --no-color > $BACKUP_DIR/docker-compose.log
docker compose logs --no-color gateway-api > $BACKUP_DIR/gateway-api.log
docker compose logs --no-color yolo-api > $BACKUP_DIR/yolo-api.log
docker compose logs --no-color edocr2-v2-api > $BACKUP_DIR/edocr2-api.log

# 시스템 정보
docker compose ps > $BACKUP_DIR/containers_status.txt
docker stats --no-stream > $BACKUP_DIR/containers_stats.txt
df -h > $BACKUP_DIR/disk_usage.txt
free -h > $BACKUP_DIR/memory_usage.txt
nvidia-smi > $BACKUP_DIR/gpu_status.txt 2>/dev/null || echo "No GPU" > $BACKUP_DIR/gpu_status.txt

# 환경 설정 (비밀번호 제거)
grep -v "PASSWORD\|KEY\|SECRET" .env > $BACKUP_DIR/env_sanitized.txt

# 압축
tar -czf $BACKUP_DIR.tar.gz -C /tmp $(basename $BACKUP_DIR)
echo "로그 수집 완료: $BACKUP_DIR.tar.gz"
```

---

## 7. FAQ

### Q1: 특정 GPU만 사용하려면?

```yaml
# docker-compose.override.yml
services:
  yolo-api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']  # GPU 0번만
              capabilities: [gpu]
```

### Q2: 여러 사용자가 동시에 사용 가능한가요?

예, 가능합니다. Settings는 사용자별 독립 (localStorage), API는 다중 사용자 동시 요청 지원합니다.

### Q3: 오프라인 환경에서 사용 가능한가요?

VL API를 제외한 모든 서비스는 오프라인 사용 가능합니다.

### Q4: 백업 주기 권장?

- 설정 파일(.env): 변경 시마다
- 데이터 디렉토리: 주 1회
- 로그 파일: 월 1회 (선택)

---

## 문제 해결 체크리스트

- [ ] 로그 확인 완료
- [ ] 시스템 리소스 확인 (CPU, RAM, GPU)
- [ ] 네트워크 연결 확인
- [ ] 방화벽 설정 확인
- [ ] 환경 설정 파일(.env) 확인
- [ ] Docker 서비스 정상 작동
- [ ] 백업 파일 확보

---

**AX 도면 분석 시스템 v23.1**
© 2026 All Rights Reserved
