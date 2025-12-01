# 도커라이징 가이드 검증 방법

**작성일**: 2025-11-23
**목적**: YOLO 및 PaddleOCR 도커라이징 가이드의 효력 검증

---

## 📋 목차

1. [검증 개요](#1-검증-개요)
2. [사전 준비](#2-사전-준비)
3. [YOLO API 검증](#3-yolo-api-검증)
4. [PaddleOCR API 검증](#4-paddleocr-api-검증)
5. [통합 검증](#5-통합-검증)
6. [성능 검증](#6-성능-검증)
7. [체크리스트](#7-체크리스트)

---

## 1. 검증 개요

### 1.1 검증 목적

외주 개발자가 작성한 도커라이징 결과물이:
1. ✅ 기술 스펙을 정확히 구현했는지
2. ✅ 현재 시스템과 완전히 호환되는지
3. ✅ BlueprintFlow에서 정상 동작하는지
4. ✅ 성능 기준을 만족하는지

### 1.2 검증 레벨

| 레벨 | 내용 | 소요 시간 |
|------|------|-----------|
| L1: 기본 동작 | 빌드, 실행, 헬스체크 | 10분 |
| L2: API 스펙 | 엔드포인트 스키마 검증 | 20분 |
| L3: 시스템 통합 | Gateway API 연동 | 15분 |
| L4: BlueprintFlow | 워크플로우 실행 | 15분 |
| L5: 성능 | 처리 속도, 정확도 | 20분 |

**총 예상 시간**: 약 1시간 20분

---

## 2. 사전 준비

### 2.1 필수 도구 설치

```bash
# curl (API 테스트)
sudo apt-get install -y curl

# jq (JSON 파싱)
sudo apt-get install -y jq

# Docker 및 Docker Compose
docker --version  # Docker version 24.0+
docker-compose --version  # Docker Compose version 2.0+

# NVIDIA Docker Runtime (GPU 테스트용)
nvidia-smi  # NVIDIA Driver 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 2.2 테스트 이미지 준비

```bash
# 테스트 이미지 다운로드 또는 준비
TEST_IMAGE="/home/uproot/ax/poc/test_data/sample_drawing.jpg"

# 이미지 존재 확인
ls -lh $TEST_IMAGE
```

**권장 테스트 이미지**:
- 기계 도면 (용접 기호, 치수 포함)
- 크기: 1920x1080 이상
- 형식: JPG 또는 PNG

### 2.3 환경 변수 설정

`.env` 파일 생성 (프로젝트 루트):
```bash
# Anthropic API Key (VL API용)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI API Key (VL API용)
OPENAI_API_KEY=sk-...
```

---

## 3. YOLO API 검증

### 3.1 L1: 기본 동작 검증

#### Step 1: 빌드

```bash
cd /home/uproot/ax/poc

# YOLO API만 빌드
docker-compose build yolo-api
```

**예상 결과**:
```
[+] Building 45.2s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => [1/8] FROM python:3.11-slim
 ...
 => exporting to image
 => => naming to docker.io/library/poc-yolo-api
```

**✅ 성공 조건**:
- 빌드 에러 없음
- 이미지 생성 완료 (`docker images | grep yolo-api`)

#### Step 2: 실행

```bash
# 컨테이너 실행
docker-compose up -d yolo-api

# 로그 확인
docker logs yolo-api --tail 50
```

**예상 출력**:
```
✅ YOLO model loaded: /app/models/best.pt
✅ YOLO loaded on cuda
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5005 (Press CTRL+C to quit)
```

**✅ 성공 조건**:
- "YOLO model loaded" 메시지 표시
- "Uvicorn running" 메시지 표시
- 에러 로그 없음

#### Step 3: 헬스체크

```bash
# 컨테이너 상태 확인
docker ps | grep yolo-api
```

**예상 출력**:
```
CONTAINER ID   IMAGE          STATUS                    PORTS
abc123         poc-yolo-api   Up 1 minute (healthy)     0.0.0.0:5005->5005/tcp
```

**✅ 성공 조건**:
- STATUS에 "(healthy)" 표시
- 포트 5005 정상 노출

```bash
# 헬스체크 엔드포인트 직접 호출
curl -s http://localhost:5005/api/v1/health | jq
```

**예상 응답**:
```json
{
  "status": "healthy",
  "service": "yolo-api",
  "version": "1.0.0",
  "model_loaded": true,
  "gpu_available": true
}
```

**✅ 성공 조건**:
- HTTP 200 OK
- `model_loaded: true`
- `gpu_available: true` (GPU 환경 시)

---

### 3.2 L2: API 스펙 검증

#### Test 1: `/api/v1/info` 메타데이터

```bash
curl -s http://localhost:5005/api/v1/info | jq > /tmp/yolo_info.json
cat /tmp/yolo_info.json
```

**검증 항목**:
```bash
# 1. id 필드 확인
jq '.id' /tmp/yolo_info.json
# 예상: "yolo"

# 2. endpoint 확인
jq '.endpoint' /tmp/yolo_info.json
# 예상: "/api/v1/detect"

# 3. inputs 확인
jq '.inputs | length' /tmp/yolo_info.json
# 예상: 1

jq '.inputs[0].name' /tmp/yolo_info.json
# 예상: "image"

# 4. parameters 확인
jq '.parameters | length' /tmp/yolo_info.json
# 예상: 6

jq '.parameters | map(.name)' /tmp/yolo_info.json
# 예상: ["model_type", "confidence", "iou", "imgsz", "visualize", "task"]

# 5. blueprintflow 메타데이터 확인
jq '.blueprintflow.color' /tmp/yolo_info.json
# 예상: "#10b981"
```

**✅ 성공 조건**:
- 모든 필드가 가이드 스펙과 정확히 일치
- JSON 스키마 유효

#### Test 2: `/api/v1/detect` 객체 검출

```bash
curl -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@$TEST_IMAGE" \
  -F "confidence=0.5" \
  -F "visualize=true" \
  -s | jq > /tmp/yolo_detect.json

cat /tmp/yolo_detect.json
```

**검증 항목**:
```bash
# 1. status 확인
jq '.status' /tmp/yolo_detect.json
# 예상: "success"

# 2. detections 배열 확인
jq '.detections | length' /tmp/yolo_detect.json
# 예상: 0 이상 (도면에 따라 다름)

# 3. detections 구조 확인 (첫 번째 요소)
jq '.detections[0] | keys' /tmp/yolo_detect.json
# 예상: ["area", "bbox", "class_id", "class_name", "confidence"]

# 4. visualization 확인
jq '.visualization | startswith("data:image/jpeg;base64,")' /tmp/yolo_detect.json
# 예상: true

# 5. processing_time 확인
jq '.processing_time < 2.0' /tmp/yolo_detect.json
# 예상: true (GPU 모드 시)
```

**✅ 성공 조건**:
- HTTP 200 OK
- `detections` 배열 구조 정확
- `visualization` base64 이미지 포함
- `processing_time < 2초` (GPU 모드)

#### Test 3: 시각화 이미지 다운로드

```bash
# base64 → 이미지 파일로 저장
jq -r '.visualization' /tmp/yolo_detect.json | \
  sed 's/data:image\/jpeg;base64,//' | \
  base64 -d > /tmp/yolo_visualization.jpg

# 이미지 파일 확인
file /tmp/yolo_visualization.jpg
# 예상: /tmp/yolo_visualization.jpg: JPEG image data

# 이미지 크기 확인
du -h /tmp/yolo_visualization.jpg
# 예상: 50K ~ 500K
```

**✅ 성공 조건**:
- JPEG 파일 정상 생성
- 파일 크기 > 0

---

### 3.3 L3: 시스템 통합 검증

#### Test 1: Docker 네트워크 통신

```bash
# Gateway API 컨테이너에서 YOLO API 호출
docker exec -it gateway-api bash -c \
  "curl -s http://yolo-api:5005/api/v1/health" | jq
```

**✅ 성공 조건**:
- 컨테이너 간 통신 성공
- HTTP 200 OK

#### Test 2: Gateway API 연동

```bash
# Gateway API를 통한 YOLO 호출 (실제 파이프라인)
curl -X POST "http://localhost:8000/api/v1/process" \
  -F "file=@$TEST_IMAGE" \
  -F "pipeline_mode=yolo_only" \
  -s | jq
```

**✅ 성공 조건**:
- Gateway API → YOLO API 통신 성공
- 검출 결과 반환

---

### 3.4 L4: BlueprintFlow 검증

#### Test 1: Auto Discover

```bash
# Gateway API의 /api/v1/blueprintflow/apis 호출
curl -s http://localhost:8000/api/v1/blueprintflow/apis | jq
```

**검증 항목**:
```bash
# YOLO API 포함 여부 확인
curl -s http://localhost:8000/api/v1/blueprintflow/apis | \
  jq '.[] | select(.id == "yolo")'
```

**예상 출력**:
```json
{
  "id": "yolo",
  "name": "YOLO",
  "display_name": "YOLO Detection",
  "endpoint": "/api/v1/detect",
  ...
}
```

**✅ 성공 조건**:
- YOLO API가 목록에 포함
- 메타데이터 정확

#### Test 2: 워크플로우 실행

1. **웹 UI 접속**:
   ```
   http://localhost:5173/blueprintflow/builder
   ```

2. **워크플로우 생성**:
   - ImageInput 노드 추가
   - YOLO 노드 추가
   - ImageInput.image → YOLO.image 연결

3. **실행 및 검증**:
   - "Execute Workflow" 버튼 클릭
   - 결과 패널에서 `detections` 배열 확인
   - 시각화 이미지 다운로드 가능 확인

**✅ 성공 조건**:
- 워크플로우 실행 에러 없음
- YOLO 노드 결과에 검출 객체 표시
- 시각화 이미지 생성

---

### 3.5 L5: 성능 검증

#### Test 1: 추론 속도

```bash
# 10회 반복 테스트
for i in {1..10}; do
  curl -X POST "http://localhost:5005/api/v1/detect" \
    -F "file=@$TEST_IMAGE" \
    -F "confidence=0.5" \
    -s | jq -r '.processing_time'
done | awk '{sum+=$1} END {print "평균:", sum/NR, "초"}'
```

**✅ 성공 조건**:
- GPU 모드: 평균 < 1.0초
- CPU 모드: 평균 < 5.0초

#### Test 2: 검출 정확도

```bash
# Ground Truth 검출 개수 (수동 확인)
GROUND_TRUTH=5  # 예: 도면에 실제 심볼 5개

# YOLO 검출 개수
DETECTED=$(curl -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@$TEST_IMAGE" \
  -F "confidence=0.5" \
  -s | jq '.detections | length')

# Recall 계산
echo "Recall: $DETECTED / $GROUND_TRUTH"
```

**✅ 성공 조건**:
- Recall > 80% (confidence=0.5 기준)

---

## 4. PaddleOCR API 검증

### 4.1 L1: 기본 동작 검증

#### Step 1: 빌드

```bash
docker-compose build paddleocr-api
```

**✅ 성공 조건**: 빌드 에러 없음

#### Step 2: 실행

```bash
docker-compose up -d paddleocr-api
docker logs paddleocr-api --tail 50
```

**예상 출력**:
```
✅ PaddleOCR loaded (GPU: True, Lang: en)
✅ PaddleOCR initialized (GPU: True, Lang: en)
INFO:     Uvicorn running on http://0.0.0.0:5006
```

**✅ 성공 조건**:
- "PaddleOCR initialized" 메시지 표시
- 에러 로그 없음

#### Step 3: 헬스체크

```bash
docker ps | grep paddleocr-api
curl -s http://localhost:5006/api/v1/health | jq
```

**예상 응답**:
```json
{
  "status": "healthy",
  "service": "paddleocr-api",
  "version": "1.0.0",
  "gpu_available": true,
  "models_loaded": {
    "det": true,
    "rec": true,
    "cls": true
  }
}
```

**✅ 성공 조건**:
- HTTP 200 OK
- 모든 모델 loaded: true

---

### 4.2 L2: API 스펙 검증

#### Test 1: `/api/v1/info` 메타데이터

```bash
curl -s http://localhost:5006/api/v1/info | jq > /tmp/paddleocr_info.json

# 검증
jq '.id' /tmp/paddleocr_info.json  # 예상: "paddleocr"
jq '.parameters | length' /tmp/paddleocr_info.json  # 예상: 6
```

**✅ 성공 조건**: 가이드 스펙과 일치

#### Test 2: `/api/v1/ocr` OCR 수행

```bash
curl -X POST "http://localhost:5006/api/v1/ocr" \
  -F "file=@$TEST_IMAGE" \
  -F "lang=en" \
  -F "min_confidence=0.5" \
  -F "visualize=true" \
  -s | jq > /tmp/paddleocr_result.json

# 검증
jq '.status' /tmp/paddleocr_result.json  # 예상: "success"
jq '.text_results | length' /tmp/paddleocr_result.json  # 예상: 0 이상
jq '.text_results[0] | keys' /tmp/paddleocr_result.json
# 예상: ["angle", "bbox", "confidence", "text"]
```

**✅ 성공 조건**:
- HTTP 200 OK
- `text_results` 배열 구조 정확
- `visualization` 포함

---

### 4.3 L3-L5: 통합/성능 검증

YOLO와 동일한 방식으로 진행:
- L3: Docker 네트워크 통신
- L4: BlueprintFlow 워크플로우
- L5: OCR 속도 (< 2초), 정확도 테스트

---

## 5. 통합 검증

### 5.1 전체 시스템 테스트

#### Test 1: 모든 서비스 동시 실행

```bash
# 전체 시스템 재시작
docker-compose down
docker-compose up -d

# 모든 컨테이너 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**예상 출력**:
```
NAMES               STATUS                   PORTS
gateway-api         Up 2 minutes (healthy)   0.0.0.0:8000->8000/tcp
yolo-api            Up 2 minutes (healthy)   0.0.0.0:5005->5005/tcp
paddleocr-api       Up 2 minutes (healthy)   0.0.0.0:5006->5006/tcp
edocr2-api          Up 2 minutes (healthy)   0.0.0.0:5001->5001/tcp
vl-api              Up 2 minutes (healthy)   0.0.0.0:5004->5004/tcp
...
```

**✅ 성공 조건**:
- 모든 컨테이너 STATUS: healthy
- 포트 충돌 없음

#### Test 2: 복합 워크플로우

**워크플로우**:
```
[ImageInput] ──┬──→ [YOLO] ──→ [PaddleOCR] ──→ [Merge]
               │
               └──→ [EDOCr2] ─────────────────→
```

**실행**:
1. BlueprintFlow Builder 접속
2. 위 워크플로우 생성
3. 실행

**✅ 성공 조건**:
- 모든 노드 실행 성공
- Merge 노드에 모든 결과 통합
- 에러 없음

---

## 6. 성능 검증

### 6.1 처리 시간 벤치마크

```bash
# 테스트 스크립트
cat > /tmp/benchmark.sh <<'EOF'
#!/bin/bash

IMAGE=$1
ITERATIONS=${2:-10}

echo "YOLO 성능 테스트..."
for i in $(seq 1 $ITERATIONS); do
  curl -X POST "http://localhost:5005/api/v1/detect" \
    -F "file=@$IMAGE" -s | jq -r '.processing_time'
done | awk '{sum+=$1} END {printf "YOLO 평균: %.3f초\n", sum/NR}'

echo ""
echo "PaddleOCR 성능 테스트..."
for i in $(seq 1 $ITERATIONS); do
  curl -X POST "http://localhost:5006/api/v1/ocr" \
    -F "file=@$IMAGE" -s | jq -r '.processing_time'
done | awk '{sum+=$1} END {printf "PaddleOCR 평균: %.3f초\n", sum/NR}'
EOF

chmod +x /tmp/benchmark.sh
/tmp/benchmark.sh $TEST_IMAGE 10
```

**예상 출력**:
```
YOLO 성능 테스트...
YOLO 평균: 0.823초

PaddleOCR 성능 테스트...
PaddleOCR 평균: 1.245초
```

**✅ 성공 조건**:
- YOLO < 1.5초
- PaddleOCR < 2.0초

---

### 6.2 메모리 사용량

```bash
# 컨테이너 리소스 모니터링
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"
```

**예상 출력**:
```
NAME              MEM USAGE        CPU %
yolo-api          2.5GiB / 8GiB    15.2%
paddleocr-api     1.8GiB / 8GiB    12.5%
```

**✅ 성공 조건**:
- 메모리 사용량 < 4GiB (각 API)

---

## 7. 체크리스트

### 7.1 YOLO API 검증 체크리스트

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

---

### 7.2 PaddleOCR API 검증 체크리스트

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

### 7.3 통합 검증 체크리스트

- [ ] 모든 서비스 동시 실행 성공
- [ ] 포트 충돌 없음
- [ ] 복합 워크플로우 (YOLO + PaddleOCR) 성공
- [ ] 전체 시스템 안정성 (1시간 연속 실행)

---

## 8. 최종 검증 보고서 템플릿

### 검증 결과 요약

```markdown
# 도커라이징 검증 보고서

**검증 일시**: 2025-11-23
**검증자**: [이름]
**환경**: Ubuntu 22.04, Docker 24.0, NVIDIA A100 40GB

## YOLO API 검증 결과

| 항목 | 결과 | 비고 |
|------|------|------|
| L1: 기본 동작 | ✅ PASS | - |
| L2: API 스펙 | ✅ PASS | - |
| L3: 시스템 통합 | ✅ PASS | - |
| L4: BlueprintFlow | ✅ PASS | - |
| L5: 성능 | ✅ PASS | 평균 0.82초 |

## PaddleOCR API 검증 결과

| 항목 | 결과 | 비고 |
|------|------|------|
| L1: 기본 동작 | ✅ PASS | - |
| L2: API 스펙 | ✅ PASS | - |
| L3: 시스템 통합 | ✅ PASS | - |
| L4: BlueprintFlow | ✅ PASS | - |
| L5: 성능 | ✅ PASS | 평균 1.24초 |

## 통합 검증 결과

- ✅ 전체 시스템 안정성 확인
- ✅ 복합 워크플로우 정상 동작
- ✅ 성능 기준 만족

## 결론

**도커라이징 가이드 효력: ✅ 검증 완료**

모든 검증 항목을 통과했으며, 현재 시스템과 완전히 호환됩니다.
```

---

**작성일**: 2025-11-23
**예상 검증 시간**: 1시간 20분
