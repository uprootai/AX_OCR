---
sidebar_position: 4
title: 관리자 매뉴얼
description: 서비스 관리, Docker 컨테이너 운영, 모니터링, 로그 관리, 백업/복구, 문제 해결
tags: [배포, 운영, 관리자, 매뉴얼]
---

# 관리자 매뉴얼 (Admin Manual)

> 서비스 관리, Docker 컨테이너 운영, 모니터링, 로그 관리, 백업/복구, 문제 해결 절차를 정리한다.

---

## 1. 시스템 개요

### 1.1 시스템 구성

AX 도면 분석 시스템은 20개 API 서비스로 구성된 마이크로서비스 아키텍처입니다.

**주요 구성 요소:**

| 카테고리 | 서비스 | 포트 | GPU |
|----------|--------|------|-----|
| **Frontend** | Web UI | 5173 | - |
| **Orchestrator** | Gateway API | 8000 | - |
| **Detection** | YOLO | 5005 | Yes |
| **OCR** | eDOCr2 | 5002 | Yes |
| **OCR** | PaddleOCR | 5006 | Yes |
| **OCR** | Tesseract | 5008 | - |
| **OCR** | TrOCR | 5009 | Yes |
| **OCR** | ESRGAN | 5010 | Yes |
| **OCR** | OCR Ensemble | 5011 | - |
| **OCR** | Surya OCR | 5013 | - |
| **OCR** | DocTR | 5014 | - |
| **OCR** | EasyOCR | 5015 | Yes |
| **Segmentation** | EDGNet | 5012 | Yes |
| **Segmentation** | Line Detector | 5016 | - |
| **Analysis** | SkinModel | 5003 | - |
| **Analysis** | PID Analyzer | 5018 | - |
| **Analysis** | Design Checker | 5019 | - |
| **Analysis** | Blueprint AI BOM | 5020 | - |
| **Knowledge** | Knowledge | 5007 | - |
| **AI** | VL | 5004 | - |

### 1.2 시스템 아키텍처

```
사용자
  |
Web UI (5173)
  |
Gateway API (8000)
  |
┌─────────────────────────────────────────────────┐
│  Detection  │  OCR (8개)  │  Analysis  │  AI   │
│    YOLO     │   eDOCr2    │  SkinModel │  VL   │
│   (5005)    │   (5002)    │   (5003)   │(5004) │
│             │  PaddleOCR  │ PID Analyzer       │
│             │   (5006)    │   (5018)           │
│             │    ...      │    ...             │
└─────────────────────────────────────────────────┘
```

---

## 2. 서비스 관리

### 2.1 서비스 상태 확인

**방법 1: Web UI Dashboard**

1. http://localhost:5173 접속
2. API Status Monitor에서 실시간 상태 확인
   - Healthy: 정상 (녹색)
   - Unhealthy: 오류 (적색)
   - Unknown: 확인 중 (회색)

**방법 2: CLI 명령어**

```bash
# 모든 서비스 상태 확인
docker compose ps

# 헬스체크 (개별 서비스)
curl http://localhost:8000/health      # Gateway
curl http://localhost:5005/health      # YOLO
curl http://localhost:5002/api/v2/health  # eDOCr2
curl http://localhost:5006/health      # PaddleOCR
```

### 2.2 서비스 시작/중지

```bash
# 전체 서비스 시작
docker compose up -d

# 전체 서비스 중지
docker compose down

# 특정 서비스만 재시작
docker compose restart yolo-api
docker compose restart edocr2-v2-api

# 선택적 서비스 시작
docker compose up -d gateway-api yolo-api edocr2-v2-api
```

### 2.3 API 테스트

```bash
# Gateway를 통한 분석
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@test_drawing.png"

# YOLO 직접 호출
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@test_drawing.png" \
  -F "model_type=engineering"

# eDOCr2 직접 호출
curl -X POST http://localhost:5002/api/v2/process \
  -F "file=@test_drawing.png" \
  -F "language=ko"
```

---

## 3. Docker 컨테이너 관리

### 3.1 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너
docker ps

# 모든 컨테이너 (중지 포함)
docker ps -a

# 리소스 사용량 실시간 확인
docker stats

# 특정 컨테이너 상세 정보
docker inspect yolo-api
```

### 3.2 로그 확인

```bash
# 실시간 로그
docker logs -f gateway-api

# 최근 100줄
docker logs --tail=100 yolo-api

# 모든 서비스 로그
docker compose logs -f
```

### 3.3 리소스 정리

```bash
# 중지된 컨테이너 제거
docker container prune

# 사용하지 않는 이미지 제거
docker image prune -a

# 전체 정리 (주의: 볼륨 제외)
docker system prune -a
```

---

## 4. 모니터링

### 4.1 시스템 리소스 확인

```bash
# CPU/메모리 사용량
htop
# 또는
top

# 디스크 사용량
df -h

# GPU 상태 (NVIDIA)
nvidia-smi
watch -n 1 nvidia-smi  # 실시간 모니터링
```

### 4.2 Docker 리소스 모니터링

```bash
# 컨테이너별 리소스 사용량
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 특정 컨테이너만
docker stats yolo-api edocr2-v2-api
```

### 4.3 헬스체크 스크립트

```bash
#!/bin/bash
# health_check.sh

SERVICES=(
  "Gateway:8000/health"
  "YOLO:5005/health"
  "eDOCr2:5002/api/v2/health"
  "SkinModel:5003/health"
  "VL:5004/health"
  "PaddleOCR:5006/health"
  "Knowledge:5007/health"
  "EDGNet:5012/health"
)

echo "=== AX System Health Check ==="
for svc in "${SERVICES[@]}"; do
  name="${svc%%:*}"
  endpoint="${svc#*:}"
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$endpoint" 2>/dev/null)
  if [ "$status" = "200" ]; then
    echo "$name: Healthy"
  else
    echo "$name: Unhealthy ($status)"
  fi
done
```

---

## 5. 로그 관리

### 5.1 로그 위치

- **Docker 로그**: `docker logs <container>`
- **애플리케이션 로그**: 각 컨테이너 내부 `/app/logs/`

### 5.2 로그 수집

```bash
# 전체 로그 수집
mkdir -p /tmp/ax-logs
docker compose logs --no-color > /tmp/ax-logs/all.log
docker compose logs gateway-api > /tmp/ax-logs/gateway.log
docker compose logs yolo-api > /tmp/ax-logs/yolo.log

# 압축
tar -czf ax-logs-$(date +%Y%m%d).tar.gz /tmp/ax-logs/
```

### 5.3 로그 정리

```bash
# Docker 로그 크기 제한 (.env에 추가)
# DOCKER_LOG_MAX_SIZE=10m
# DOCKER_LOG_MAX_FILE=3

# 오래된 로그 삭제
find /var/lib/docker/containers -name "*.log" -mtime +30 -delete
```

---

## 6. 백업 및 복구

### 6.1 백업 대상

| 항목 | 위치 | 우선순위 |
|------|------|----------|
| 환경 설정 | `.env` | 필수 |
| Docker 설정 | `docker-compose.yml` | 필수 |
| 모델 가중치 | `models/*/models/` | 필수 |
| 데이터 | `data/` | 권장 |

### 6.2 백업 실행

```bash
# 백업 디렉토리 생성
BACKUP_DIR=/opt/ax-backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# 설정 파일 백업
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/
cp -r docker-compose.override.yml $BACKUP_DIR/ 2>/dev/null

# 모델 파일 백업 (용량 큼)
# cp -r models/*/models/ $BACKUP_DIR/models/

# 압축
tar -czf $BACKUP_DIR.tar.gz -C /opt/ax-backups $(basename $BACKUP_DIR)
```

### 6.3 복구

```bash
# 압축 해제
tar -xzf backup_20260117.tar.gz

# 설정 복원
cp backup_20260117/.env .
cp backup_20260117/docker-compose.yml .

# 서비스 재시작
docker compose down
docker compose up -d
```

---

## 7. 문제 해결

### 7.1 서비스 시작 실패

```bash
# 로그 확인
docker compose logs <service-name>

# 포트 충돌 확인
sudo lsof -i :5005
sudo netstat -tulpn | grep 5005

# 컨테이너 재생성
docker compose down
docker compose up -d --force-recreate
```

### 7.2 GPU 인식 안 됨

```bash
# 호스트 GPU 확인
nvidia-smi

# Docker GPU 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# nvidia-container-toolkit 재설치
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

### 7.3 메모리 부족

```bash
# 메모리 사용량 확인
free -h
docker stats

# .env에서 메모리 제한 조정
# YOLO_MEMORY=2g
# EDOCR2_MEMORY=2g

# 불필요한 서비스 중지
docker compose stop edgnet-api paddleocr-api
```

### 7.4 API 응답 느림

```bash
# GPU 사용률 확인
nvidia-smi

# CPU 사용률 확인
top

# 서비스 재시작
docker compose restart yolo-api
```

---

## 8. FAQ

### Q1. 특정 GPU만 사용하려면?

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

### Q2. 오프라인 환경에서 사용 가능한가요?

네, VL API를 제외한 모든 서비스는 오프라인 사용 가능합니다.

### Q3. 동시 사용자 수 제한이 있나요?

기본적으로 제한 없습니다. GPU 메모리에 따라 동시 처리 성능이 달라집니다.

### Q4. 자동 백업 설정 방법?

```bash
# crontab -e
0 2 * * * /opt/ax-drawing-analysis/scripts/backup.sh
```

## 관련 문서

- [시스템 설치 가이드](/docs/deployment/installation) — 설치 절차 및 환경 설정
- [온프레미스 운영 가이드](/docs/deployment/on-premise-operation) — 교육, 백업, 업데이트
- [온프레미스 인프라 구성](/docs/deployment/on-premise-infra) — 하드웨어 및 보안 요구사항
- [Docker Compose](/docs/devops/docker-compose) — 컨테이너 오케스트레이션
