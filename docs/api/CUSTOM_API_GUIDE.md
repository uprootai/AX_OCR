# API 커스터마이징 가이드

> **목적**: YOLO, PaddleOCR 등 개별 API를 자체 구현으로 교체하는 방법
> **대상**: AI 모델 개발자, 백엔드 개발자
> **난이도**: 중급 (FastAPI, Docker 경험 필요)
> **예상 소요 시간**: 2-4시간

---

## 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [교체 가능한 API 목록](#2-교체-가능한-api-목록)
3. [YOLO API 교체 가이드](#3-yolo-api-교체-가이드)
4. [PaddleOCR API 교체 가이드](#4-paddleocr-api-교체-가이드)
5. [일반 API 교체 체크리스트](#5-일반-api-교체-체크리스트)
6. [테스트 및 검증](#6-테스트-및-검증)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 아키텍처 개요

### 1.1 레이어 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  web-ui/src/config/nodeDefinitions.ts                       │
│  - 노드 UI 정의, 파라미터 설정                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Gateway API (FastAPI)                        │
│  gateway-api/blueprintflow/executors/*_executor.py          │
│  - 워크플로우 실행, 노드 오케스트레이션                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  gateway-api/services/*_service.py                          │
│  - HTTP 클라이언트, API 호출 추상화                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Individual API Services (Docker)                │
│  models/{api-name}-api/api_server.py                        │
│  - 실제 AI 모델 실행, 추론                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 파일 위치 요약

| 레이어 | 위치 | 역할 |
|--------|------|------|
| API 서버 | `models/{api-name}-api/` | 실제 AI 모델 실행 |
| API 스펙 | `gateway-api/api_specs/{api-name}.yaml` | 메타데이터, 파라미터 정의 |
| 서비스 | `gateway-api/services/{api}_service.py` | HTTP 클라이언트 |
| Executor | `gateway-api/blueprintflow/executors/` | 워크플로우 통합 |
| 노드 정의 | `web-ui/src/config/nodeDefinitions.ts` | UI 파라미터 |
| Docker | `docker-compose.yml` | 컨테이너 설정 |

---

## 2. 교체 가능한 API 목록

| API | 포트 | 카테고리 | 복잡도 |
|-----|------|----------|--------|
| YOLO | 5005 | Detection | 높음 (다중 모델) |
| PaddleOCR | 5006 | OCR | 중간 |
| eDOCr2 | 5002 | OCR | 중간 |
| ESRGAN | 5010 | Preprocessing | 낮음 |
| Tesseract | 5008 | OCR | 낮음 |

---

## 3. YOLO API 교체 가이드

### 3.1 요구사항

- **필수 엔드포인트**: `POST /api/v1/detect`
- **헬스체크**: `GET /api/v1/health`
- **정보**: `GET /api/v1/info` (권장)

### 3.2 입력 형식 (Request)

```
Method: POST /api/v1/detect
Content-Type: multipart/form-data

Parameters:
  file: <이미지 바이너리>           # 필수
  confidence: float (0.0-1.0)     # 기본값: 0.4
  iou: float (0.0-1.0)            # 기본값: 0.5
  imgsz: int                      # 기본값: 1024
  model_type: string              # 기본값: "bom_detector"
  task: string                    # 기본값: "detect"
  visualize: boolean              # 기본값: true
  use_sahi: boolean               # 기본값: false (선택)
  slice_height: int               # SAHI용 (선택)
  slice_width: int                # SAHI용 (선택)
  overlap_ratio: float            # SAHI용 (선택)
```

### 3.3 출력 형식 (Response)

```json
{
  "status": "success",
  "file_id": "uuid-string",
  "detections": [
    {
      "class_id": 0,
      "class_name": "차단기",
      "confidence": 0.95,
      "bbox": {
        "x": 100,
        "y": 200,
        "width": 50,
        "height": 80
      },
      "value": null
    }
  ],
  "total_detections": 10,
  "processing_time": 0.234,
  "model_used": "bom_detector",
  "image_size": {
    "width": 3508,
    "height": 2480
  },
  "visualized_image": "base64_encoded_string_or_null"
}
```

### 3.4 최소 구현 예제

```python
# models/my-detector-api/api_server.py

from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import base64
import uuid

app = FastAPI(title="My Custom Detector API")

class BBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox
    value: Optional[str] = None

class DetectionResponse(BaseModel):
    status: str
    file_id: str
    detections: List[Detection]
    total_detections: int
    processing_time: float
    model_used: str
    image_size: dict
    visualized_image: Optional[str] = None

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/info")
async def info():
    return {
        "models": ["my_model_v1"],
        "default_model": "my_model_v1",
        "supported_tasks": ["detect"]
    }

@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect(
    file: UploadFile = File(...),
    confidence: float = Form(0.4),
    iou: float = Form(0.5),
    imgsz: int = Form(1024),
    model_type: str = Form("my_model_v1"),
    task: str = Form("detect"),
    visualize: bool = Form(True),
):
    import time
    start_time = time.time()

    # 이미지 읽기
    image_bytes = await file.read()

    # TODO: 여기에 실제 모델 추론 로직 구현
    # 예: detections = your_model.predict(image_bytes, confidence, iou)

    detections = [
        Detection(
            class_id=0,
            class_name="example_class",
            confidence=0.95,
            bbox=BBox(x=100, y=100, width=50, height=50)
        )
    ]

    processing_time = time.time() - start_time

    # 시각화 이미지 생성 (선택)
    visualized_image = None
    if visualize:
        # TODO: 바운딩 박스 그린 이미지를 base64로 인코딩
        pass

    return DetectionResponse(
        status="success",
        file_id=str(uuid.uuid4()),
        detections=detections,
        total_detections=len(detections),
        processing_time=processing_time,
        model_used=model_type,
        image_size={"width": 1000, "height": 1000},  # 실제 이미지 크기로 교체
        visualized_image=visualized_image
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)
```

### 3.5 Dockerfile 예제

```dockerfile
# models/my-detector-api/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 (OpenCV 등)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5005

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5005"]
```

### 3.6 requirements.txt 예제

```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pillow==10.1.0
numpy==1.24.3
# TODO: 실제 모델 의존성 추가 (ultralytics, torch 등)
```

### 3.7 docker-compose.yml 수정

```yaml
services:
  my-detector-api:
    build: ./models/my-detector-api
    container_name: my-detector-api
    ports:
      - "5005:5005"  # YOLO 포트 재사용 또는 새 포트
    networks:
      - ax_poc_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5005/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 3.8 API 스펙 작성 (선택)

자동 통합을 위해 API 스펙을 작성하면 `GenericAPIExecutor`가 자동으로 연동합니다.

```yaml
# gateway-api/api_specs/my-detector.yaml

api_id: my-detector
name: My Custom Detector
version: "1.0.0"
port: 5005
description: "커스텀 객체 검출 API"

server:
  endpoint: "/api/v1/detect"
  method: "POST"
  content_type: "multipart/form-data"
  health_endpoint: "/api/v1/health"
  timeout: 60

inputs:
  - name: image
    type: image
    required: true

outputs:
  - name: detections
    type: array
  - name: visualized_image
    type: image

parameters:
  - name: confidence
    label: "신뢰도 임계값"
    type: number
    default: 0.4
    min: 0.05
    max: 1.0
    step: 0.05
  - name: model_type
    label: "모델 선택"
    type: select
    default: "my_model_v1"
    options:
      - value: "my_model_v1"
        label: "My Model v1"

mappings:
  detections: "detections"
  visualized_image: "visualized_image"

blueprintflow:
  icon: "Target"
  color: "#10b981"
  category: "detection"
```

---

## 4. PaddleOCR API 교체 가이드

### 4.1 입력 형식

```
Method: POST /api/v1/ocr
Content-Type: multipart/form-data

Parameters:
  file: <이미지 바이너리>           # 필수
  det_db_thresh: float            # 텍스트 검출 임계값
  det_db_box_thresh: float        # 박스 임계값
  use_angle_cls: boolean          # 각도 분류 사용
  min_confidence: float           # 최소 신뢰도
  visualize: boolean              # 시각화 여부
```

### 4.2 출력 형식

```json
{
  "status": "success",
  "processing_time": 0.45,
  "total_texts": 15,
  "detections": [
    {
      "text": "인식된 텍스트",
      "confidence": 0.98,
      "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
      "position": {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 30
      }
    }
  ],
  "visualized_image": "base64_string",
  "metadata": {}
}
```

### 4.3 최소 구현 예제

```python
# models/my-ocr-api/api_server.py

from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="My Custom OCR API")

class TextDetection(BaseModel):
    text: str
    confidence: float
    bbox: List[List[float]]
    position: dict

class OCRResponse(BaseModel):
    status: str
    processing_time: float
    total_texts: int
    detections: List[TextDetection]
    visualized_image: Optional[str] = None
    metadata: dict = {}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/ocr", response_model=OCRResponse)
async def ocr(
    file: UploadFile = File(...),
    det_db_thresh: float = Form(0.3),
    det_db_box_thresh: float = Form(0.5),
    use_angle_cls: bool = Form(True),
    min_confidence: float = Form(0.5),
    visualize: bool = Form(True),
):
    import time
    start_time = time.time()

    image_bytes = await file.read()

    # TODO: 실제 OCR 로직 구현
    detections = []

    return OCRResponse(
        status="success",
        processing_time=time.time() - start_time,
        total_texts=len(detections),
        detections=detections,
        visualized_image=None,
        metadata={}
    )
```

---

## 5. 일반 API 교체 체크리스트

### 5.1 필수 작업

- [ ] FastAPI 서버 생성 (`api_server.py`)
- [ ] 메인 엔드포인트 구현 (`/api/v1/{action}`)
- [ ] 헬스체크 엔드포인트 (`/api/v1/health`)
- [ ] Pydantic 응답 모델 정의
- [ ] `requirements.txt` 작성
- [ ] `Dockerfile` 작성
- [ ] `docker-compose.yml` 서비스 추가

### 5.2 선택 작업 (권장)

- [ ] API 스펙 YAML 파일 작성 (`api_specs/`)
- [ ] 정보 엔드포인트 (`/api/v1/info`)
- [ ] 시각화 이미지 반환
- [ ] 에러 핸들링 및 로깅
- [ ] 단위 테스트 작성

### 5.3 통합 작업 (고급)

- [ ] 커스텀 Executor 작성 (필요시)
- [ ] 서비스 레이어 함수 추가
- [ ] 노드 정의 추가 (`nodeDefinitions.ts`)

---

## 6. 테스트 및 검증

### 6.1 API 단독 테스트

```bash
# 1. 컨테이너 빌드 및 실행
docker-compose build my-detector-api
docker-compose up -d my-detector-api

# 2. 헬스체크
curl http://localhost:5005/api/v1/health

# 3. 검출 테스트
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@test_image.jpg" \
  -F "confidence=0.4" \
  -F "visualize=true"
```

### 6.2 BlueprintFlow 통합 테스트

```bash
# Gateway API에서 API 호출 테스트
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test",
    "nodes": [
      {
        "id": "input",
        "type": "image-input",
        "data": {"image": "base64..."}
      },
      {
        "id": "detect",
        "type": "my-detector",
        "data": {"confidence": 0.4}
      }
    ],
    "edges": [
      {"source": "input", "target": "detect"}
    ]
  }'
```

### 6.3 검증 항목

| 항목 | 확인 방법 |
|------|----------|
| 응답 형식 | JSON 구조가 기존 API와 동일한가? |
| 바운딩 박스 | `bbox`가 `{x, y, width, height}` 형식인가? |
| 시각화 | `visualized_image`가 base64 인코딩인가? |
| 에러 처리 | 잘못된 입력에 적절한 HTTP 에러 반환? |
| 성능 | 처리 시간이 허용 범위 내인가? |

---

## 7. 트러블슈팅

### 7.1 일반적인 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| 422 Unprocessable Entity | 파라미터 타입 불일치 | Form 파라미터 타입 확인 |
| 500 Internal Server Error | 모델 로딩 실패 | 로그 확인, GPU 메모리 |
| Connection Refused | 컨테이너 미실행 | `docker-compose up -d` |
| 빈 검출 결과 | 신뢰도 너무 높음 | confidence 값 낮춤 |

### 7.2 bbox 형식 불일치

기존 API와 bbox 형식이 다른 경우 변환 필요:

```python
# [x1, y1, x2, y2] → {x, y, width, height}
def convert_bbox(x1, y1, x2, y2):
    return {
        "x": x1,
        "y": y1,
        "width": x2 - x1,
        "height": y2 - y1
    }

# [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] → {x, y, width, height}
def convert_polygon_bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "x": min(xs),
        "y": min(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys)
    }
```

### 7.3 Docker 네트워크 문제

```bash
# 네트워크 확인
docker network ls | grep ax_poc

# 컨테이너 네트워크 연결 확인
docker inspect my-detector-api | grep NetworkMode

# 수동 네트워크 연결
docker network connect ax_poc_network my-detector-api
```

---

## 부록: 스캐폴딩 스크립트

새 API를 빠르게 생성하려면:

```bash
# 스캐폴딩 스크립트 사용
python scripts/create_api.py my-detector --port 5005 --category detection

# 생성되는 파일:
# - models/my-detector-api/api_server.py
# - models/my-detector-api/Dockerfile
# - models/my-detector-api/requirements.txt
# - gateway-api/api_specs/my-detector.yaml
```

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-17
**작성자**: Claude Code (Opus 4.5)
