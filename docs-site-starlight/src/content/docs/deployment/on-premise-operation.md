---
sidebar_position: 3
title: 온프레미스 운영 가이드
description: 고객사 교육 계획, 자동 백업/복구, 업데이트 절차, 트러블슈팅, 성능 튜닝
tags: [배포, 운영, 온프레미스, 운영가이드]
---

# 온프레미스 운영 가이드 (On-Premise Operations)

> 고객사 교육 계획, 자동 백업/복구, 업데이트 절차, 트러블슈팅, 성능 튜닝을 정리한다.

---

## 1. 고객사 교육 계획

### 1.1 교육 과정 (2일)

#### Day 1: 운영자 교육

**시간표**:
```
09:00 - 09:30  오리엔테이션 및 시스템 소개
09:30 - 10:30  시스템 아키텍처 이해
10:30 - 10:45  휴식
10:45 - 12:00  Admin Dashboard 사용법

12:00 - 13:00  점심

13:00 - 14:00  Grafana 모니터링 대시보드
14:00 - 15:00  Docker 관리 (시작/중지/재시작)
15:00 - 15:15  휴식
15:15 - 16:30  로그 분석 및 기본 트러블슈팅
16:30 - 17:00  Q&A 및 실습
```

**실습 내용**:
1. 도면 업로드 및 처리
2. Admin Dashboard에서 시스템 상태 확인
3. Grafana에서 메트릭 조회
4. Docker 컨테이너 재시작
5. 로그 파일 확인

#### Day 2: 관리자 교육

**시간표**:
```
09:00 - 10:00  모델 재학습 방법
10:00 - 11:00  백업/복구 실습
11:00 - 12:00  성능 튜닝 및 최적화

12:00 - 13:00  점심

13:00 - 14:00  보안 설정 및 권한 관리
14:00 - 15:00  시스템 업그레이드 방법
15:00 - 15:15  휴식
15:15 - 16:30  장애 대응 시나리오 실습
16:30 - 17:00  종합 Q&A 및 수료증 발급
```

**실습 내용**:
1. EDGNet 모델 재학습
2. 전체 시스템 백업 생성
3. 백업에서 복구
4. API 키 추가/삭제
5. 모의 장애 대응

### 1.2 교육 자료

```
training/
├── slides/
│   ├── Day1_시스템소개.pptx
│   ├── Day1_운영자교육.pptx
│   ├── Day2_관리자교육.pptx
│   └── Day2_장애대응.pptx
│
├── hands-on/
│   ├── 01_첫도면처리.md
│   ├── 02_모니터링.md
│   ├── 03_백업복구.md
│   └── 04_장애시나리오.md
│
└── cheat-sheets/
    ├── docker-commands.pdf
    ├── grafana-queries.pdf
    └── troubleshooting-guide.pdf
```

---

## 2. 백업

### 2.1 자동 백업 스크립트

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/opt/ax-system/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ax-system-backup-$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

mkdir -p "$BACKUP_PATH"

echo "백업 시작: $BACKUP_NAME"

# 1. Docker 볼륨 백업
docker run --rm \
  -v ax-system_models:/data \
  -v "$BACKUP_PATH":/backup \
  alpine tar czf /backup/models.tar.gz -C /data .

# 2. 설정 파일 백업
tar czf "$BACKUP_PATH/config.tar.gz" /opt/ax-system/config

# 3. Prometheus 데이터 백업
tar czf "$BACKUP_PATH/prometheus.tar.gz" /opt/ax-system/prometheus-data

# 4. Grafana 데이터 백업
tar czf "$BACKUP_PATH/grafana.tar.gz" /opt/ax-system/grafana-data

# 5. 감사 로그 백업
tar czf "$BACKUP_PATH/audit-logs.tar.gz" /opt/ax-system/logs

# 6. 메타데이터
echo "$TIMESTAMP" > "$BACKUP_PATH/metadata.txt"
echo "Hostname: $(hostname)" >> "$BACKUP_PATH/metadata.txt"
docker-compose config > "$BACKUP_PATH/docker-compose.yml"

echo "백업 완료: $BACKUP_PATH"

# 오래된 백업 삭제 (30일 이상)
find "$BACKUP_DIR" -type d -name "ax-system-backup-*" -mtime +30 -exec rm -rf {} \;
```

### 2.2 Cron 설정 (매일 자동 백업)

```bash
# crontab -e
0 2 * * * /opt/ax-system/scripts/backup.sh >> /opt/ax-system/logs/backup.log 2>&1
```

---

## 3. 복구

```bash
#!/bin/bash
# scripts/restore.sh

if [ -z "$1" ]; then
    echo "사용법: $0 <백업디렉토리>"
    echo "예시: $0 /opt/ax-system/backups/ax-system-backup-20251114_020000"
    exit 1
fi

BACKUP_PATH="$1"

echo "복구 시작: $BACKUP_PATH"

# 시스템 중지
cd /opt/ax-system
docker-compose down

# 복구
tar xzf "$BACKUP_PATH/models.tar.gz" -C /opt/ax-system/data/models
tar xzf "$BACKUP_PATH/config.tar.gz" -C /
tar xzf "$BACKUP_PATH/prometheus.tar.gz" -C /opt/ax-system
tar xzf "$BACKUP_PATH/grafana.tar.gz" -C /opt/ax-system

# 시스템 시작
docker-compose up -d

echo "복구 완료"
```

---

## 4. 업데이트

```bash
#!/bin/bash
# scripts/update.sh

NEW_VERSION="$1"

if [ -z "$NEW_VERSION" ]; then
    echo "사용법: $0 <버전>"
    echo "예시: $0 1.1.0"
    exit 1
fi

echo "업데이트 시작: v$NEW_VERSION"

# 1. 백업
./scripts/backup.sh

# 2. 새 이미지 로드
docker load < updates/v$NEW_VERSION/*.tar

# 3. Docker Compose 업데이트
cp updates/v$NEW_VERSION/docker-compose.yml /opt/ax-system/

# 4. 재시작
cd /opt/ax-system
docker-compose up -d

echo "업데이트 완료"
```

---

## 5. 트러블슈팅

| 증상 | 원인 | 해결 방법 |
|------|------|----------|
| GPU out of memory | VRAM 부족 | batch_size 줄이기, 불필요한 모델 종료 |
| API 응답 느림 | 높은 부하 | 리소스 증설, 파이프라인 모드 변경 |
| Docker 시작 실패 | 포트 충돌 | `netstat -tulpn`으로 확인, 포트 변경 |

### 서비스 시작 실패

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

### GPU 인식 안 됨

```bash
# 호스트 GPU 확인
nvidia-smi

# Docker GPU 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# nvidia-container-toolkit 재설치
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

### 메모리 부족

```bash
# 메모리 사용량 확인
free -h
docker stats

# 불필요한 서비스 중지
docker compose stop edgnet-api paddleocr-api
```

---

## 6. 성능 튜닝

```yaml
# docker-compose.yml
services:
  gateway-api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

### GPU 메모리 최적화

```python
# 모델 로드 시 FP16 사용
self.model = YOLO(model_path)
self.model.to(self.device)
self.model.half()  # FP32 -> FP16 (메모리 절반)
```

### 이미지 크기 조정

```bash
# imgsz 파라미터를 줄여서 처리 속도 향상
# 1280 -> 640으로 변경 시 약 4배 속도 향상
```

---

## 7. Docker 재빌드 상태

### 재빌드 호환성

| Component | Docker Rebuild 후 상태 | 작동 여부 |
|-----------|-------------------|---------|
| **Frontend (web-ui)** | 정상 작동 | 모든 파라미터 표시됨 |
| **Backend APIs** | 부분 작동 | 새 파라미터 무시됨 |
| **기존 기능** | 정상 작동 | 영향 없음 |

### 재빌드 명령

```bash
# 1. 이전 컨테이너 정지
docker-compose down

# 2. 캐시 없이 재빌드 (권장)
docker-compose build --no-cache

# 3. 서비스 시작
docker-compose up -d

# 4. 로그 확인
docker-compose logs -f web-ui

# 5. Health Check
curl http://localhost:8000/api/v1/health
curl http://localhost:5173
```

### 재빌드 후 검증

```bash
# Frontend 확인
# http://localhost:5173/blueprintflow/builder 접속
# YOLO 노드 클릭 -> Detail Panel에 파라미터 확인

# Backend 확인
curl http://localhost:5005/health  # YOLO API
curl http://localhost:5002/health  # eDOCr2 API
# 기존 워크플로우 실행 -> 결과 정상 반환
```

---

## 8. Feature Matrix (Docker 재빌드 후)

| Feature | Frontend | Backend | 실제 작동 |
|---------|----------|---------|---------|
| **기존 기능** | Yes | Yes | 정상 |
| **새 파라미터 UI 표시** | Yes | - | 표시됨 |
| **새 파라미터 처리** | Yes | No | 무시됨 |
| **YOLO 특화 모델** | Yes | No | 사용 안 됨 |
| **eDOCr2 선택적 추출** | Yes | No | 최적화 안 됨 |
| **워크플로우 실행** | Yes | Yes | 작동 |
| **결과 반환** | Yes | Yes | 반환됨 |

---

## 9. 라이선스

```
상업적 라이선스
온프레미스 단일 서버 라이선스
```

## 관련 문서

- [온프레미스 인프라 구성](/deployment/on-premise-infra) — 하드웨어 및 보안 요구사항
- [관리자 매뉴얼](/deployment/admin-manual) — 서비스 관리 및 모니터링
- [시스템 설치 가이드](/deployment/installation) — 설치 절차 및 환경 설정
- [Dockerization](/deployment/dockerization) — Docker 컨테이너화 가이드
