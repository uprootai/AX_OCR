---
sidebar_position: 5
title: Dockerization 통합 가이드
description: YOLO API, PaddleOCR API 도커라이징, 검증 레벨(L1~L5), 트러블슈팅
---

# Dockerization 통합 가이드

> YOLO API와 PaddleOCR API의 도커라이징, 검증 레벨(L1~L5), 트러블슈팅을 정리한다.

---

## 목차

1. [Docker Rebuild 상태](#docker-rebuild-상태)
2. [YOLO API 도커라이징](#yolo-api-도커라이징)
3. [PaddleOCR API 도커라이징](#paddleocr-api-도커라이징)
4. [검증 방법](#검증-방법)
5. [통합 검증](#통합-검증)
6. [트러블슈팅](#트러블슈팅)

---

## Docker Rebuild 상태

### 현재 상태 요약

| Component | Docker Rebuild 후 상태 | 작동 여부 |
|-----------|-------------------|---------|
| **Frontend (web-ui)** | 정상 작동 | 31개 파라미터 모두 표시됨 |
| **Backend APIs** | 부분 작동 | 새 파라미터 무시됨 |
| **기존 기능** | 정상 작동 | 영향 없음 |

**결론**: Docker 재빌드 가능하며, **Frontend는 정상**, **Backend는 새 파라미터만 아직 처리 안 됨**

### Docker 재빌드 명령

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

### Feature Matrix (Docker 재빌드 후)

| Feature | Frontend | Backend | 실제 작동 |
|---------|----------|---------|---------|
| **기존 기능** | O | O | 정상 |
| **새 파라미터 UI 표시** | O | - | 표시됨 |
| **새 파라미터 처리** | O | X | 무시됨 |
| **YOLO 특화 모델** | O | X | 사용 안 됨 |
| **eDOCr2 선택적 추출** | O | X | 최적화 안 됨 |
| **워크플로우 실행** | O | O | 작동 |
| **결과 반환** | O | O | 반환됨 |

---

## YOLO API 도커라이징

### 현재 시스템 구조

```
/home/uproot/ax/poc/models/yolo-api/
├── Dockerfile                 # Docker 이미지 빌드 파일
├── requirements.txt           # Python 패키지 목록
├── api_server.py              # FastAPI 서버 (메인 파일)
├── models/                    # YOLO 모델 저장소
│   ├── best.pt                # 학습된 심볼 검출 모델
│   └── yolo11n.pt             # 일반 YOLO 모델 (백업용)
├── services/                  # 비즈니스 로직
│   └── yolo_service.py        # YOLO 추론 로직
├── utils/                     # 유틸리티
│   ├── image_utils.py         # 이미지 전처리
│   └── visualization.py       # 검출 결과 시각화
├── uploads/                   # 임시 업로드 (Volume 마운트)
└── results/                   # 결과 저장 (Volume 마운트)
```

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/health` | GET | 헬스체크 |
| `/api/v1/info` | GET | API 메타데이터 (BlueprintFlow Auto Discover) |
| `/api/v1/detect` | POST | 객체 검출 (이미지 -> 검출 결과) |

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_server.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

RUN mkdir -p /tmp/yolo-api/uploads /tmp/yolo-api/results /app/models

RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

EXPOSE 5005

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5005/api/v1/health || exit 1

CMD ["python", "api_server.py"]
```

### docker-compose 설정

```yaml
services:
  yolo-api:
    build:
      context: ./models/yolo-api
      dockerfile: Dockerfile
    container_name: yolo-api
    ports:
      - "5005:5005"
    volumes:
      - ./models/yolo-api/models:/app/models:ro
      - ./models/yolo-api/uploads:/tmp/yolo-api/uploads
      - ./models/yolo-api/results:/tmp/yolo-api/results
    environment:
      - YOLO_API_PORT=5005
      - YOLO_MODEL_PATH=/app/models/best.pt
      - PYTHONUNBUFFERED=1
    networks:
      - ax_poc_network
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5005/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Request/Response 스키마

**POST `/api/v1/detect`**

Request (multipart/form-data):
```
file: <image_file>
model_type: "symbol-detector-v1"  (선택)
confidence: 0.5  (선택)
iou: 0.45  (선택)
imgsz: 640  (선택)
visualize: true  (선택)
task: "detect"  (선택)
```

Response:
```json
{
  "status": "success",
  "detections": [
    {
      "class_name": "welding_symbol",
      "class_id": 0,
      "confidence": 0.92,
      "bbox": {
        "x1": 120,
        "y1": 340,
        "x2": 180,
        "y2": 400
      },
      "area": 3600
    }
  ],
  "visualization": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "model_used": "symbol-detector-v1",
  "image_size": [1920, 1080],
  "processing_time": 0.23
}
```

### 빌드 및 실행

```bash
# 빌드
cd /home/uproot/ax/poc
docker-compose build yolo-api

# 실행
docker-compose up -d yolo-api

# 로그 확인
docker logs yolo-api -f

# 헬스체크
curl http://localhost:5005/api/v1/health
```

---

## PaddleOCR API 도커라이징

### 디렉토리 구조

```
/home/uproot/ax/poc/models/paddleocr-api/
├── Dockerfile
├── requirements.txt
├── api_server.py
├── services/
│   └── paddleocr_service.py
├── utils/
│   ├── image_utils.py
│   └── visualization.py
├── uploads/
└── results/
```

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/health` | GET | 헬스체크 |
| `/api/v1/info` | GET | API 메타데이터 |
| `/api/v1/ocr` | POST | OCR 수행 (이미지 -> 텍스트 추출) |

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_server.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

RUN mkdir -p /root/.paddleocr

EXPOSE 5006

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5006/api/v1/health || exit 1

CMD ["python", "api_server.py"]
```

### docker-compose 설정

```yaml
services:
  paddleocr-api:
    build:
      context: ./models/paddleocr-api
      dockerfile: Dockerfile
    container_name: paddleocr-api
    ports:
      - "5006:5006"
    volumes:
      - ./models/paddleocr-api/uploads:/tmp/paddleocr-api/uploads
      - ./models/paddleocr-api/results:/tmp/paddleocr-api/results
    environment:
      - PADDLEOCR_PORT=5006
      - USE_GPU=true
      - USE_ANGLE_CLS=true
      - OCR_LANG=en
      - PYTHONUNBUFFERED=1
    networks:
      - ax_poc_network
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5006/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Request/Response 스키마

**POST `/api/v1/ocr`**

Request (multipart/form-data):
```
file: <image_file>
lang: "en"  (선택)
det_db_thresh: 0.3  (선택)
det_db_box_thresh: 0.5  (선택)
use_angle_cls: true  (선택)
min_confidence: 0.5  (선택)
visualize: true  (선택)
```

Response:
```json
{
  "status": "success",
  "text_results": [
    {
      "text": "50mm",
      "confidence": 0.92,
      "bbox": [
        [120, 340],
        [180, 340],
        [180, 370],
        [120, 370]
      ],
      "angle": 0
    }
  ],
  "visualization": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "total_texts": 1,
  "processing_time": 0.45
}
```

### 빌드 및 실행

```bash
# 빌드
docker-compose build paddleocr-api

# 실행
docker-compose up -d paddleocr-api

# 로그 확인
docker logs paddleocr-api -f

# 헬스체크
curl http://localhost:5006/api/v1/health
```

---

## 검증 방법

### 검증 레벨

| 레벨 | 내용 | 소요 시간 |
|------|------|-----------|
| L1: 기본 동작 | 빌드, 실행, 헬스체크 | 10분 |
| L2: API 스펙 | 엔드포인트 스키마 검증 | 20분 |
| L3: 시스템 통합 | Gateway API 연동 | 15분 |
| L4: BlueprintFlow | 워크플로우 실행 | 15분 |
| L5: 성능 | 처리 속도, 정확도 | 20분 |

**총 예상 시간**: 약 1시간 20분

### L1: 기본 동작 검증

```bash
# 빌드
docker-compose build yolo-api paddleocr-api

# 실행
docker-compose up -d yolo-api paddleocr-api

# 컨테이너 상태 확인
docker ps | grep -E "yolo-api|paddleocr-api"

# 헬스체크
curl -s http://localhost:5005/api/v1/health | jq
curl -s http://localhost:5006/api/v1/health | jq
```

### L2: API 스펙 검증

```bash
# YOLO API 메타데이터
curl -s http://localhost:5005/api/v1/info | jq

# PaddleOCR API 메타데이터
curl -s http://localhost:5006/api/v1/info | jq

# YOLO 검출 테스트
curl -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@test_image.jpg" \
  -F "confidence=0.5" \
  -F "visualize=true" | jq

# PaddleOCR 테스트
curl -X POST "http://localhost:5006/api/v1/ocr" \
  -F "file=@test_image.jpg" \
  -F "lang=en" \
  -F "min_confidence=0.5" | jq
```

### L3: 시스템 통합 검증

```bash
# Gateway API를 통한 통합 테스트
curl http://localhost:8000/api/v1/health | jq

# Docker 네트워크 통신 확인
docker exec -it gateway-api bash -c \
  "curl -s http://yolo-api:5005/api/v1/health"

docker exec -it gateway-api bash -c \
  "curl -s http://paddleocr-api:5006/api/v1/health"
```

### L4: BlueprintFlow 검증

1. **웹 UI 접속**: `http://localhost:5173/blueprintflow/builder`
2. **워크플로우 생성**: ImageInput -> YOLO -> PaddleOCR -> Merge
3. **실행 및 검증**: 모든 노드 정상 실행 확인

### L5: 성능 검증

```bash
# YOLO 성능 테스트 (10회)
for i in {1..10}; do
  curl -X POST "http://localhost:5005/api/v1/detect" \
    -F "file=@test_image.jpg" \
    -F "confidence=0.5" \
    -s | jq -r '.processing_time'
done | awk '{sum+=$1} END {print "YOLO 평균:", sum/NR, "초"}'

# PaddleOCR 성능 테스트 (10회)
for i in {1..10}; do
  curl -X POST "http://localhost:5006/api/v1/ocr" \
    -F "file=@test_image.jpg" \
    -s | jq -r '.processing_time'
done | awk '{sum+=$1} END {print "PaddleOCR 평균:", sum/NR, "초"}'
```

**성능 기준:**
- YOLO < 1.5초 (GPU 모드)
- PaddleOCR < 2.0초 (GPU 모드)
- 메모리 사용량 < 4GiB (각 API)

---

## 통합 검증

### 전체 시스템 테스트

```bash
# 전체 시스템 재시작
docker-compose down
docker-compose up -d

# 모든 컨테이너 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 리소스 모니터링
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"
```

### YOLO API 검증 체크리스트

#### L1: 기본 동작
- [ ] 빌드 성공
- [ ] 컨테이너 실행 성공
- [ ] 헬스체크 정상 (healthy)
- [ ] 모델 로드 성공
- [ ] GPU 인식 (GPU 환경 시)

#### L2: API 스펙
- [ ] `/api/v1/health` 스펙 일치
- [ ] `/api/v1/info` 메타데이터 정확
- [ ] `/api/v1/detect` 응답 구조 정확
- [ ] `detections` 배열 파싱 가능
- [ ] `visualization` 이미지 생성

#### L3: 시스템 통합
- [ ] Docker 네트워크 통신 성공
- [ ] Gateway API 연동 성공
- [ ] 파이프라인 모드 동작

#### L4: BlueprintFlow
- [ ] Auto Discover 인식
- [ ] 대시보드 표시
- [ ] 워크플로우 실행 성공
- [ ] 노드 결과 표시

#### L5: 성능
- [ ] 추론 속도 < 1.5초 (GPU 모드)
- [ ] 검출 정확도 > 80%
- [ ] 메모리 사용량 < 4GiB

### PaddleOCR API 검증 체크리스트

#### L1: 기본 동작
- [ ] 빌드 성공
- [ ] 컨테이너 실행 성공
- [ ] 헬스체크 정상
- [ ] 모델 로드 성공 (det, rec, cls)
- [ ] GPU 인식

#### L2: API 스펙
- [ ] `/api/v1/health` 스펙 일치
- [ ] `/api/v1/info` 메타데이터 정확
- [ ] `/api/v1/ocr` 응답 구조 정확
- [ ] `text_results` 배열 파싱 가능
- [ ] `visualization` 이미지 생성

#### L3: 시스템 통합
- [ ] Docker 네트워크 통신 성공
- [ ] Gateway API 연동 성공

#### L4: BlueprintFlow
- [ ] Auto Discover 인식
- [ ] 워크플로우 실행 성공

#### L5: 성능
- [ ] OCR 속도 < 2.0초 (GPU 모드)
- [ ] 인식 정확도 > 70%

---

## 트러블슈팅

### 모델 로드 실패

**증상**:
```
Failed to load YOLO model: [Errno 2] No such file or directory: '/app/models/best.pt'
```

**해결**:
```bash
# 모델 파일 확인
ls -lh /home/uproot/ax/poc/models/yolo-api/models/best.pt

# Volume 마운트 확인
docker inspect yolo-api | jq '.[0].Mounts'

# 재빌드
docker-compose build yolo-api
docker-compose up -d yolo-api
```

### GPU 인식 안됨

**증상**: `"gpu_available": false`

**해결**:
```bash
# NVIDIA Docker Runtime 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# docker-compose.yml GPU 설정 확인
# deploy.resources.reservations.devices 항목 확인

# 재시작
docker-compose restart yolo-api
```

### 헬스체크 실패

**증상**: STATUS: (unhealthy)

**해결**: `--start-period` 값을 40s에서 60s로 증가

### 추론 속도 느림

**해결**:
1. GPU 활성화 확인
2. `imgsz` 파라미터 축소 (1280 -> 640)
3. FP16 모드 사용: `self.model.half()`

### 메모리 부족

**증상**: `torch.cuda.OutOfMemoryError`

**해결**:
```python
# FP16 사용 (메모리 절반)
self.model = YOLO(model_path)
self.model.to(self.device)
self.model.half()
```

### PaddleOCR 모델 다운로드 실패

**해결**: 인터넷 연결 확인 후 재시도 (첫 실행 시 자동 다운로드)

### 한국어 인식 안됨

**해결**: `lang="korean"` 설정
```python
PaddleOCR(lang="korean")
```

---

## 관련 문서

- [Docker Compose](/devops/docker-compose) — 컨테이너 오케스트레이션 설정
- [GPU 설정](/devops/gpu-config) — 서비스별 GPU 할당
- [시스템 설치 가이드](/deployment/installation) — 설치 절차 및 환경 설정
- [API 교체 가이드](/developer/api-replacement) — API 교체 및 마이그레이션
