# YOLO API 도커라이징 가이드

**작성일**: 2025-11-23
**대상**: 외주 개발자
**목적**: YOLO API를 현재 시스템과 호환되는 Docker 컨테이너로 패키징

---

## 📋 목차

1. [현재 시스템 구조](#1-현재-시스템-구조)
2. [요구사항](#2-요구사항)
3. [Dockerfile 작성](#3-dockerfile-작성)
4. [디렉토리 구조](#4-디렉토리-구조)
5. [API 서버 구현](#5-api-서버-구현)
6. [docker-compose 통합](#6-docker-compose-통합)
7. [테스트 방법](#7-테스트-방법)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 현재 시스템 구조

### 1.1 전체 아키텍처

```
/home/uproot/ax/poc/
├── models/
│   ├── yolo-api/              ← 현재 YOLO API 위치
│   │   ├── Dockerfile         ← 수정 대상
│   │   ├── api_server.py      ← FastAPI 서버
│   │   ├── requirements.txt
│   │   ├── models/            ← YOLO 모델 저장소
│   │   │   └── best.pt        ← 학습된 모델
│   │   ├── services/          ← 비즈니스 로직
│   │   └── utils/             ← 유틸리티
│   ├── paddleocr-api/
│   ├── edocr2-api/
│   └── ...
├── gateway-api/               ← 오케스트레이터
└── docker-compose.yml         ← 통합 설정
```

### 1.2 현재 YOLO API 스펙

**기존 Dockerfile** (`models/yolo-api/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api_server.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

# Create directories
RUN mkdir -p /tmp/yolo-api/uploads /tmp/yolo-api/results /app/models

# Download YOLOv11n as default model (for prototype)
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5005/api/v1/health || exit 1

# Run server
CMD ["python", "api_server.py"]
```

**포트**: 5005
**GPU 지원**: ✅ (NVIDIA Docker Runtime)
**Health Check 엔드포인트**: `GET /api/v1/health`

---

## 2. 요구사항

### 2.1 필수 요구사항

#### A. API 엔드포인트 호환성

YOLO API는 **반드시** 다음 엔드포인트를 제공해야 합니다:

| 엔드포인트 | 메서드 | 설명 | 우선순위 |
|-----------|--------|------|---------|
| `/api/v1/health` | GET | 헬스체크 | 🔴 필수 |
| `/api/v1/info` | GET | API 메타데이터 (BlueprintFlow Auto Discover) | 🔴 필수 |
| `/api/v1/detect` | POST | 객체 검출 (이미지 → 검출 결과) | 🔴 필수 |

#### B. Request/Response 스키마

**1. `/api/v1/health` (GET)**

Response:
```json
{
  "status": "healthy",
  "service": "yolo-api",
  "version": "1.0.0",
  "model_loaded": true,
  "gpu_available": true
}
```

**2. `/api/v1/info` (GET)**

Response:
```json
{
  "id": "yolo",
  "name": "YOLO",
  "display_name": "YOLO Detection",
  "endpoint": "/api/v1/detect",
  "method": "POST",
  "requires_image": true,

  "inputs": [
    {
      "name": "image",
      "type": "file",
      "required": true,
      "description": "도면 이미지 파일 (JPG, PNG 등)"
    }
  ],

  "outputs": [
    {
      "name": "detections",
      "type": "array",
      "description": "검출된 객체 목록"
    },
    {
      "name": "visualization",
      "type": "string",
      "description": "시각화 이미지 (base64)"
    }
  ],

  "parameters": [
    {
      "name": "model_type",
      "type": "select",
      "default": "symbol-detector-v1",
      "options": [
        "symbol-detector-v1",
        "dimension-detector-v1",
        "gdt-detector-v1",
        "text-region-detector-v1",
        "yolo11n-general"
      ],
      "description": "용도별 특화 모델"
    },
    {
      "name": "confidence",
      "type": "number",
      "default": 0.5,
      "min": 0.0,
      "max": 1.0,
      "description": "검출 신뢰도 임계값"
    },
    {
      "name": "iou",
      "type": "number",
      "default": 0.45,
      "min": 0.0,
      "max": 1.0,
      "description": "NMS IoU 임계값"
    },
    {
      "name": "imgsz",
      "type": "number",
      "default": 640,
      "min": 320,
      "max": 1280,
      "description": "입력 이미지 크기"
    },
    {
      "name": "visualize",
      "type": "boolean",
      "default": true,
      "description": "검출 결과 시각화 이미지 생성"
    },
    {
      "name": "task",
      "type": "select",
      "default": "detect",
      "options": ["detect", "segment"],
      "description": "작업 종류"
    }
  ],

  "blueprintflow": {
    "icon": "🎯",
    "color": "#10b981",
    "category": "api"
  }
}
```

**3. `/api/v1/detect` (POST)**

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
    },
    {
      "class_name": "bearing",
      "class_id": 5,
      "confidence": 0.87,
      "bbox": {
        "x1": 450,
        "y1": 280,
        "x2": 520,
        "y2": 350
      },
      "area": 4900
    }
  ],
  "visualization": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "model_used": "symbol-detector-v1",
  "image_size": [1920, 1080],
  "processing_time": 0.23
}
```

#### C. 환경변수

```bash
YOLO_API_PORT=5005                    # 필수
YOLO_MODEL_PATH=/app/models/best.pt   # 필수
PYTHONUNBUFFERED=1                    # 권장 (로그 즉시 출력)
```

#### D. Volume 마운트

```yaml
volumes:
  - ./models/yolo-api/models:/app/models:ro         # 모델 파일 (읽기 전용)
  - ./models/yolo-api/uploads:/tmp/yolo-api/uploads # 업로드 임시 파일
  - ./models/yolo-api/results:/tmp/yolo-api/results # 결과 저장
```

#### E. GPU 지원

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

---

### 2.2 권장 사항

1. **모델 캐싱**: 모델을 메모리에 로드한 상태 유지 (요청마다 로드 금지)
2. **비동기 처리**: FastAPI의 async/await 사용
3. **에러 처리**: 명확한 HTTP 상태 코드 및 에러 메시지
4. **로깅**: 구조화된 로그 (JSON 형식 권장)
5. **타임아웃**: 추론 시간 30초 이내

---

## 3. Dockerfile 작성

### 3.1 Base Image 선택

**권장**: `python:3.11-slim` 또는 `nvidia/cuda:12.1.0-runtime-ubuntu22.04`

GPU 사용 시:
```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Python 설치
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
```

CPU 전용:
```dockerfile
FROM python:3.11-slim
```

### 3.2 시스템 의존성 설치

```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
```

**중요**:
- `curl`: 헬스체크용 필수
- `libgl1`, `libglib2.0-0`: OpenCV 의존성

### 3.3 Python 패키지 설치

`requirements.txt` 예시:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pillow==10.1.0
numpy==1.26.2
opencv-python-headless==4.8.1.78
ultralytics==8.1.0  # YOLOv11
torch==2.1.0
torchvision==0.16.0
pydantic==2.5.0
```

Dockerfile:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### 3.4 애플리케이션 복사

```dockerfile
WORKDIR /app

COPY api_server.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/
```

### 3.5 디렉토리 생성

```dockerfile
RUN mkdir -p /tmp/yolo-api/uploads /tmp/yolo-api/results /app/models
```

### 3.6 헬스체크 설정

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5005/api/v1/health || exit 1
```

**파라미터 설명**:
- `--interval`: 30초마다 체크
- `--timeout`: 10초 내 응답 없으면 실패
- `--start-period`: 시작 후 40초 동안은 실패 무시 (초기화 시간)
- `--retries`: 3번 연속 실패 시 unhealthy

### 3.7 포트 노출

```dockerfile
EXPOSE 5005
```

### 3.8 실행 명령

```dockerfile
CMD ["python", "api_server.py"]
```

또는 Uvicorn 직접 실행:
```dockerfile
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5005"]
```

---

## 4. 디렉토리 구조

### 4.1 필수 구조

```
models/yolo-api/
├── Dockerfile                 # Docker 이미지 빌드 파일
├── requirements.txt           # Python 패키지 목록
├── api_server.py              # FastAPI 서버 (메인 파일)
├── models/                    # YOLO 모델 저장소
│   ├── best.pt                # 학습된 심볼 검출 모델
│   ├── dimension-v1.pt        # 치수 검출 모델 (선택)
│   ├── gdt-v1.pt              # GD&T 검출 모델 (선택)
│   └── yolo11n.pt             # 일반 YOLO 모델 (백업용)
├── services/                  # 비즈니스 로직
│   ├── __init__.py
│   └── yolo_service.py        # YOLO 추론 로직
├── utils/                     # 유틸리티
│   ├── __init__.py
│   ├── image_utils.py         # 이미지 전처리
│   └── visualization.py       # 검출 결과 시각화
├── uploads/                   # 임시 업로드 (Volume 마운트)
└── results/                   # 결과 저장 (Volume 마운트)
```

### 4.2 .dockerignore

불필요한 파일 제외:
```
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.gitignore
.vscode/
.idea/
uploads/*
results/*
*.log
*.tmp
```

---

## 5. API 서버 구현

### 5.1 api_server.py 기본 구조

```python
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import os
import time
import base64
from pathlib import Path

# Services
from services.yolo_service import YOLODetector
from utils.image_utils import load_image, preprocess_image
from utils.visualization import draw_detections

# =====================
# Configuration
# =====================
YOLO_API_PORT = int(os.getenv("YOLO_API_PORT", 5005))
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "/app/models/best.pt")

# =====================
# FastAPI App
# =====================
app = FastAPI(
    title="YOLO Detection API",
    description="YOLOv11 기반 기계 도면 심볼 검출 API",
    version="1.0.0"
)

# =====================
# Global Model
# =====================
detector: Optional[YOLODetector] = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 YOLO 모델 로드"""
    global detector
    try:
        detector = YOLODetector(model_path=YOLO_MODEL_PATH)
        print(f"✅ YOLO model loaded: {YOLO_MODEL_PATH}")
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        raise

# =====================
# Pydantic Models
# =====================
class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class Detection(BaseModel):
    class_name: str
    class_id: int
    confidence: float
    bbox: BBox
    area: float

class DetectResponse(BaseModel):
    status: str
    detections: List[Detection]
    visualization: Optional[str] = None
    model_used: str
    image_size: List[int]
    processing_time: float

# =====================
# Endpoints
# =====================
@app.get("/api/v1/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "yolo-api",
        "version": "1.0.0",
        "model_loaded": detector is not None,
        "gpu_available": detector.is_gpu_available() if detector else False
    }

@app.get("/api/v1/info")
async def get_api_info():
    """API 메타데이터 (BlueprintFlow Auto Discover용)"""
    return {
        "id": "yolo",
        "name": "YOLO",
        "display_name": "YOLO Detection",
        "endpoint": "/api/v1/detect",
        "method": "POST",
        "requires_image": True,

        "inputs": [
            {
                "name": "image",
                "type": "file",
                "required": True,
                "description": "도면 이미지 파일 (JPG, PNG 등)"
            }
        ],

        "outputs": [
            {
                "name": "detections",
                "type": "array",
                "description": "검출된 객체 목록"
            },
            {
                "name": "visualization",
                "type": "string",
                "description": "시각화 이미지 (base64)"
            }
        ],

        "parameters": [
            {
                "name": "model_type",
                "type": "select",
                "default": "symbol-detector-v1",
                "options": [
                    "symbol-detector-v1",
                    "dimension-detector-v1",
                    "gdt-detector-v1",
                    "text-region-detector-v1",
                    "yolo11n-general"
                ],
                "description": "용도별 특화 모델"
            },
            {
                "name": "confidence",
                "type": "number",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "description": "검출 신뢰도 임계값"
            },
            {
                "name": "iou",
                "type": "number",
                "default": 0.45,
                "min": 0.0,
                "max": 1.0,
                "description": "NMS IoU 임계값"
            },
            {
                "name": "imgsz",
                "type": "number",
                "default": 640,
                "min": 320,
                "max": 1280,
                "description": "입력 이미지 크기"
            },
            {
                "name": "visualize",
                "type": "boolean",
                "default": True,
                "description": "검출 결과 시각화 이미지 생성"
            },
            {
                "name": "task",
                "type": "select",
                "default": "detect",
                "options": ["detect", "segment"],
                "description": "작업 종류"
            }
        ],

        "blueprintflow": {
            "icon": "🎯",
            "color": "#10b981",
            "category": "api"
        }
    }

@app.post("/api/v1/detect", response_model=DetectResponse)
async def detect_objects(
    file: UploadFile = File(...),
    model_type: str = Form(default="symbol-detector-v1"),
    confidence: float = Form(default=0.5, ge=0.0, le=1.0),
    iou: float = Form(default=0.45, ge=0.0, le=1.0),
    imgsz: int = Form(default=640, ge=320, le=1280),
    visualize: bool = Form(default=True),
    task: str = Form(default="detect")
):
    """
    객체 검출 API

    Args:
        file: 이미지 파일
        model_type: 모델 종류
        confidence: 신뢰도 임계값
        iou: NMS IoU 임계값
        imgsz: 이미지 크기
        visualize: 시각화 여부
        task: 작업 종류 (detect/segment)

    Returns:
        DetectResponse: 검출 결과
    """
    if not detector:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()
        image = load_image(image_bytes)

        # YOLO 추론
        results = detector.detect(
            image,
            confidence=confidence,
            iou=iou,
            imgsz=imgsz,
            task=task
        )

        # 결과 파싱
        detections = []
        for det in results:
            detections.append(Detection(
                class_name=det["class_name"],
                class_id=det["class_id"],
                confidence=det["confidence"],
                bbox=BBox(**det["bbox"]),
                area=det["area"]
            ))

        # 시각화
        visualization_base64 = None
        if visualize and len(detections) > 0:
            vis_image = draw_detections(image, results)
            visualization_base64 = f"data:image/jpeg;base64,{base64.b64encode(vis_image).decode()}"

        processing_time = time.time() - start_time

        return DetectResponse(
            status="success",
            detections=detections,
            visualization=visualization_base64,
            model_used=model_type,
            image_size=[image.shape[1], image.shape[0]],
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

# =====================
# Main
# =====================
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=YOLO_API_PORT,
        log_level="info"
    )
```

### 5.2 services/yolo_service.py

```python
from ultralytics import YOLO
import torch
import numpy as np
from typing import List, Dict, Any

class YOLODetector:
    def __init__(self, model_path: str):
        """
        YOLO 모델 초기화

        Args:
            model_path: 모델 파일 경로
        """
        self.model = YOLO(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"✅ YOLO loaded on {self.device}")

    def is_gpu_available(self) -> bool:
        return torch.cuda.is_available()

    def detect(
        self,
        image: np.ndarray,
        confidence: float = 0.5,
        iou: float = 0.45,
        imgsz: int = 640,
        task: str = "detect"
    ) -> List[Dict[str, Any]]:
        """
        객체 검출

        Args:
            image: NumPy 이미지 (H, W, C)
            confidence: 신뢰도 임계값
            iou: NMS IoU 임계값
            imgsz: 이미지 크기
            task: detect 또는 segment

        Returns:
            List[Dict]: 검출 결과 목록
        """
        results = self.model.predict(
            source=image,
            conf=confidence,
            iou=iou,
            imgsz=imgsz,
            verbose=False
        )

        detections = []
        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i])
                cls_id = int(boxes.cls[i])
                cls_name = self.model.names[cls_id]

                detections.append({
                    "class_name": cls_name,
                    "class_id": cls_id,
                    "confidence": conf,
                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2)
                    },
                    "area": float((x2 - x1) * (y2 - y1))
                })

        return detections
```

### 5.3 utils/image_utils.py

```python
import cv2
import numpy as np
from PIL import Image
import io

def load_image(image_bytes: bytes) -> np.ndarray:
    """
    바이트 데이터를 NumPy 이미지로 변환

    Args:
        image_bytes: 이미지 바이트

    Returns:
        np.ndarray: BGR 이미지
    """
    image = Image.open(io.BytesIO(image_bytes))
    image = np.array(image)

    # RGB → BGR (OpenCV 형식)
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    return image

def preprocess_image(image: np.ndarray, target_size: int = 640) -> np.ndarray:
    """
    이미지 전처리 (리사이즈)

    Args:
        image: 입력 이미지
        target_size: 목표 크기

    Returns:
        np.ndarray: 전처리된 이미지
    """
    h, w = image.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)

    resized = cv2.resize(image, (new_w, new_h))
    return resized
```

### 5.4 utils/visualization.py

```python
import cv2
import numpy as np
from typing import List, Dict, Any

def draw_detections(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    thickness: int = 2
) -> bytes:
    """
    검출 결과를 이미지에 그리기

    Args:
        image: 원본 이미지
        detections: 검출 결과 목록
        thickness: 선 두께

    Returns:
        bytes: JPEG 인코딩된 이미지
    """
    vis_image = image.copy()

    for det in detections:
        bbox = det["bbox"]
        x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
        class_name = det["class_name"]
        confidence = det["confidence"]

        # 바운딩 박스
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), thickness)

        # 레이블
        label = f"{class_name} {confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(vis_image, (x1, y1 - label_h - 10), (x1 + label_w, y1), (0, 255, 0), -1)
        cv2.putText(vis_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # JPEG 인코딩
    _, buffer = cv2.imencode('.jpg', vis_image)
    return buffer.tobytes()
```

---

## 6. docker-compose 통합

### 6.1 docker-compose.yml에 추가

**위치**: `/home/uproot/ax/poc/docker-compose.yml`

```yaml
services:
  # =====================
  # YOLOv11 API (포트 5005)
  # =====================
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
    # GPU 지원 활성화 ✅
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

networks:
  ax_poc_network:
    driver: bridge
```

### 6.2 네트워크 통신

Gateway API에서 YOLO API 호출 시:

```python
import httpx

async with httpx.AsyncClient() as client:
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
    data = {
        "model_type": "symbol-detector-v1",
        "confidence": 0.5,
        "visualize": True
    }

    response = await client.post(
        "http://yolo-api:5005/api/v1/detect",  # ✅ 컨테이너명 사용
        files=files,
        data=data,
        timeout=30.0
    )
```

**중요**: Docker Compose 네트워크 내에서는 서비스명(`yolo-api`)으로 통신

---

## 7. 테스트 방법

### 7.1 빌드 및 실행

```bash
# 1. 프로젝트 루트로 이동
cd /home/uproot/ax/poc

# 2. YOLO API만 빌드
docker-compose build yolo-api

# 3. YOLO API 실행
docker-compose up -d yolo-api

# 4. 로그 확인
docker logs yolo-api -f
```

**예상 출력**:
```
✅ YOLO model loaded: /app/models/best.pt
✅ YOLO loaded on cuda
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:5005
```

### 7.2 헬스체크 테스트

```bash
curl http://localhost:5005/api/v1/health
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

### 7.3 API 메타데이터 테스트

```bash
curl http://localhost:5005/api/v1/info | jq
```

**예상 응답**: `/api/v1/info` 스펙대로 출력

### 7.4 객체 검출 테스트

```bash
curl -X POST "http://localhost:5005/api/v1/detect" \
  -F "file=@/path/to/test_drawing.jpg" \
  -F "confidence=0.5" \
  -F "visualize=true" \
  | jq
```

**예상 응답**:
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

### 7.5 BlueprintFlow 통합 테스트

1. **웹 UI 접속**:
   ```
   http://localhost:5173/blueprintflow/builder
   ```

2. **워크플로우 생성**:
   - ImageInput 노드 추가, 도면 이미지 업로드
   - YOLO 노드 추가
   - ImageInput.image → YOLO.image 연결

3. **실행**:
   - "Execute Workflow" 버튼 클릭
   - YOLO 노드 결과 확인 (detections 목록)

4. **검증**:
   - `detections` 배열에 검출된 객체 표시
   - `visualize=true` 시 시각화 이미지 표시

---

## 8. 트러블슈팅

### 8.1 모델 로드 실패

**증상**:
```
❌ Failed to load YOLO model: [Errno 2] No such file or directory: '/app/models/best.pt'
```

**원인**: 모델 파일이 Volume 마운트되지 않음

**해결**:
```bash
# 1. 모델 파일 확인
ls -lh /home/uproot/ax/poc/models/yolo-api/models/best.pt

# 2. docker-compose.yml Volume 확인
volumes:
  - ./models/yolo-api/models:/app/models:ro  # ✅ 올바름

# 3. 재빌드
docker-compose build yolo-api
docker-compose up -d yolo-api
```

---

### 8.2 GPU 인식 안됨

**증상**:
```json
{
  "gpu_available": false
}
```

**원인**: NVIDIA Docker Runtime 미설치 또는 설정 오류

**해결**:
```bash
# 1. NVIDIA Docker Runtime 설치 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 2. docker-compose.yml GPU 설정 확인
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]

# 3. 재시작
docker-compose restart yolo-api
```

---

### 8.3 헬스체크 실패

**증상**:
```bash
docker ps
# STATUS: (unhealthy)
```

**원인**: 서버 시작 시간이 40초 초과

**해결**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5005/api/v1/health || exit 1
```

`--start-period=40s` → `60s`로 증가

---

### 8.4 추론 속도 느림

**증상**: `processing_time > 5.0`

**원인**: CPU 모드 또는 이미지 크기 너무 큼

**해결**:
1. GPU 활성화 확인
2. `imgsz` 파라미터 축소 (1280 → 640)
3. 배치 처리 구현 (여러 이미지 동시 처리)

---

### 8.5 메모리 부족

**증상**:
```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**해결**:
```python
# 모델 로드 시 FP16 사용
self.model = YOLO(model_path)
self.model.to(self.device)
self.model.half()  # FP32 → FP16 (메모리 절반)
```

---

## 9. 검증 체크리스트

### ✅ 기능 검증

- [ ] `/api/v1/health` 정상 응답 (200 OK)
- [ ] `/api/v1/info` BlueprintFlow 메타데이터 출력
- [ ] `/api/v1/detect` 이미지 업로드 → 검출 결과 반환
- [ ] `visualize=true` 시 시각화 이미지 생성
- [ ] GPU 모드에서 추론 속도 < 1초 (640px 이미지 기준)
- [ ] 여러 모델 전환 가능 (`model_type` 파라미터)

### ✅ Docker 통합

- [ ] `docker-compose build yolo-api` 성공
- [ ] `docker-compose up -d yolo-api` 정상 실행
- [ ] `docker ps` → STATUS: healthy
- [ ] Volume 마운트 정상 (모델 파일 읽기 성공)
- [ ] 네트워크 통신 정상 (gateway-api → yolo-api)

### ✅ BlueprintFlow 통합

- [ ] Auto Discover로 YOLO 노드 자동 인식
- [ ] 대시보드에 YOLO API 표시
- [ ] BlueprintFlow Builder에서 YOLO 노드 추가 가능
- [ ] ImageInput → YOLO 연결 → 실행 성공
- [ ] 결과 패널에 검출된 객체 목록 표시
- [ ] 시각화 이미지 다운로드 가능

---

## 10. 제출물

### 제출 파일

1. **Dockerfile** (`models/yolo-api/Dockerfile`)
2. **requirements.txt**
3. **api_server.py** (FastAPI 서버)
4. **services/yolo_service.py**
5. **utils/image_utils.py**
6. **utils/visualization.py**
7. **README.md** (간단한 실행 가이드)

### 문서

- 빌드 및 실행 로그 (`docker-compose up` 출력)
- 테스트 결과 스크린샷:
  - `/api/v1/health` 응답
  - `/api/v1/info` 응답
  - `/api/v1/detect` 검출 결과
  - BlueprintFlow 실행 결과

---

## 11. 참고 자료

- **Ultralytics YOLO 문서**: https://docs.ultralytics.com/
- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **Docker Compose 문서**: https://docs.docker.com/compose/
- **NVIDIA Docker**: https://github.com/NVIDIA/nvidia-docker

---

**작성일**: 2025-11-23
**담당자**: 외주 개발자
**검수자**: Claude Code (Sonnet 4.5)
**예상 작업 시간**: 8시간
