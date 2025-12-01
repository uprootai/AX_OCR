# PaddleOCR API 도커라이징 가이드

**작성일**: 2025-11-23
**대상**: 외주 개발자
**목적**: PaddleOCR API를 현재 시스템과 호환되는 Docker 컨테이너로 패키징

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
│   ├── paddleocr-api/         ← 현재 PaddleOCR API 위치
│   │   ├── Dockerfile         ← 수정 대상
│   │   ├── api_server.py      ← FastAPI 서버
│   │   ├── requirements.txt
│   │   ├── services/          ← 비즈니스 로직
│   │   └── utils/             ← 유틸리티
│   ├── yolo-api/
│   ├── edocr2-api/
│   └── ...
├── gateway-api/               ← 오케스트레이터
└── docker-compose.yml         ← 통합 설정
```

### 1.2 현재 PaddleOCR API 스펙

**기존 Dockerfile** (`models/paddleocr-api/Dockerfile`):
```dockerfile
# PaddleOCR API Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치 (OpenCV 및 PaddlePaddle 의존성)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY api_server.py .
COPY models/ ./models/
COPY services/ ./services/
COPY utils/ ./utils/

# PaddleOCR 모델 다운로드를 위한 디렉토리 생성
RUN mkdir -p /root/.paddleocr

# 포트 노출
EXPOSE 5006

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5006/api/v1/health || exit 1

# 서버 실행
CMD ["python", "api_server.py"]
```

**포트**: 5006
**GPU 지원**: ✅ (NVIDIA Docker Runtime)
**Health Check 엔드포인트**: `GET /api/v1/health`

---

## 2. 요구사항

### 2.1 필수 요구사항

#### A. API 엔드포인트 호환성

PaddleOCR API는 **반드시** 다음 엔드포인트를 제공해야 합니다:

| 엔드포인트 | 메서드 | 설명 | 우선순위 |
|-----------|--------|------|---------|
| `/api/v1/health` | GET | 헬스체크 | 🔴 필수 |
| `/api/v1/info` | GET | API 메타데이터 (BlueprintFlow Auto Discover) | 🔴 필수 |
| `/api/v1/ocr` | POST | OCR 수행 (이미지 → 텍스트 추출) | 🔴 필수 |

#### B. Request/Response 스키마

**1. `/api/v1/health` (GET)**

Response:
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

**2. `/api/v1/info` (GET)**

Response:
```json
{
  "id": "paddleocr",
  "name": "PaddleOCR",
  "display_name": "PaddleOCR",
  "endpoint": "/api/v1/ocr",
  "method": "POST",
  "requires_image": true,

  "inputs": [
    {
      "name": "image",
      "type": "file",
      "required": true,
      "description": "도면 이미지 또는 YOLO 검출 영역"
    }
  ],

  "outputs": [
    {
      "name": "text_results",
      "type": "array",
      "description": "인식된 텍스트 목록 (내용, 위치, 정확도)"
    },
    {
      "name": "visualization",
      "type": "string",
      "description": "OCR 결과 시각화 이미지 (base64)"
    }
  ],

  "parameters": [
    {
      "name": "lang",
      "type": "select",
      "default": "en",
      "options": ["en", "ch", "korean", "japan", "french"],
      "description": "인식 언어"
    },
    {
      "name": "det_db_thresh",
      "type": "number",
      "default": 0.3,
      "min": 0.0,
      "max": 1.0,
      "description": "텍스트 검출 임계값"
    },
    {
      "name": "det_db_box_thresh",
      "type": "number",
      "default": 0.5,
      "min": 0.0,
      "max": 1.0,
      "description": "박스 임계값"
    },
    {
      "name": "use_angle_cls",
      "type": "boolean",
      "default": true,
      "description": "회전된 텍스트 감지 여부"
    },
    {
      "name": "min_confidence",
      "type": "number",
      "default": 0.5,
      "min": 0.0,
      "max": 1.0,
      "description": "최소 신뢰도"
    },
    {
      "name": "visualize",
      "type": "boolean",
      "default": true,
      "description": "OCR 결과 시각화 이미지 생성"
    }
  ],

  "blueprintflow": {
    "icon": "📄",
    "color": "#06b6d4",
    "category": "api"
  }
}
```

**3. `/api/v1/ocr` (POST)**

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
      "text": "Ø50mm",
      "confidence": 0.92,
      "bbox": [
        [120, 340],
        [180, 340],
        [180, 370],
        [120, 370]
      ],
      "angle": 0
    },
    {
      "text": "L100±0.05",
      "confidence": 0.88,
      "bbox": [
        [450, 280],
        [560, 280],
        [560, 310],
        [450, 310]
      ],
      "angle": 0
    }
  ],
  "visualization": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "total_texts": 2,
  "processing_time": 0.45
}
```

#### C. 환경변수

```bash
PADDLEOCR_PORT=5006           # 필수
USE_GPU=true                  # 권장 (GPU 사용 여부)
USE_ANGLE_CLS=true            # 권장 (회전 감지)
OCR_LANG=en                   # 기본 언어
PYTHONUNBUFFERED=1            # 권장 (로그 즉시 출력)
```

#### D. Volume 마운트

```yaml
volumes:
  - ./models/paddleocr-api/uploads:/tmp/paddleocr-api/uploads  # 업로드 임시 파일
  - ./models/paddleocr-api/results:/tmp/paddleocr-api/results  # 결과 저장
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

1. **모델 캐싱**: PaddleOCR 인스턴스를 메모리에 로드한 상태 유지
2. **비동기 처리**: FastAPI의 async/await 사용
3. **에러 처리**: 명확한 HTTP 상태 코드 및 에러 메시지
4. **로깅**: 구조화된 로그 (JSON 형식 권장)
5. **타임아웃**: OCR 처리 시간 60초 이내

---

## 3. Dockerfile 작성

### 3.1 Base Image 선택

**권장**: `python:3.10-slim` (PaddlePaddle은 3.10에서 안정적)

```dockerfile
FROM python:3.10-slim
```

GPU 사용 시:
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Python 3.10 설치
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.10 /usr/bin/python
```

### 3.2 시스템 의존성 설치

```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*
```

**중요**:
- `curl`: 헬스체크용 필수
- `libgl1`, `libglib2.0-0`: OpenCV 의존성
- `libgomp1`: OpenMP (병렬 처리)

### 3.3 Python 패키지 설치

`requirements.txt` 예시:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pillow==10.1.0
numpy==1.26.2
opencv-python-headless==4.8.1.78
paddlepaddle-gpu==2.5.2  # GPU 버전
# paddlepaddle==2.5.2    # CPU 전용 시
paddleocr==2.7.0.3
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
COPY services/ ./services/
COPY utils/ ./utils/
```

### 3.5 PaddleOCR 모델 디렉토리 생성

```dockerfile
RUN mkdir -p /root/.paddleocr /tmp/paddleocr-api/uploads /tmp/paddleocr-api/results
```

**참고**: PaddleOCR은 첫 실행 시 자동으로 모델을 `/root/.paddleocr`에 다운로드합니다.

### 3.6 헬스체크 설정

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5006/api/v1/health || exit 1
```

### 3.7 포트 노출

```dockerfile
EXPOSE 5006
```

### 3.8 실행 명령

```dockerfile
CMD ["python", "api_server.py"]
```

---

## 4. 디렉토리 구조

### 4.1 필수 구조

```
models/paddleocr-api/
├── Dockerfile                 # Docker 이미지 빌드 파일
├── requirements.txt           # Python 패키지 목록
├── api_server.py              # FastAPI 서버 (메인 파일)
├── services/                  # 비즈니스 로직
│   ├── __init__.py
│   └── paddleocr_service.py   # PaddleOCR 추론 로직
├── utils/                     # 유틸리티
│   ├── __init__.py
│   ├── image_utils.py         # 이미지 전처리
│   └── visualization.py       # OCR 결과 시각화
├── uploads/                   # 임시 업로드 (Volume 마운트)
└── results/                   # 결과 저장 (Volume 마운트)
```

### 4.2 .dockerignore

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
from services.paddleocr_service import PaddleOCRService
from utils.image_utils import load_image
from utils.visualization import draw_ocr_results

# =====================
# Configuration
# =====================
PADDLEOCR_PORT = int(os.getenv("PADDLEOCR_PORT", 5006))
USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"
USE_ANGLE_CLS = os.getenv("USE_ANGLE_CLS", "true").lower() == "true"
OCR_LANG = os.getenv("OCR_LANG", "en")

# =====================
# FastAPI App
# =====================
app = FastAPI(
    title="PaddleOCR API",
    description="PaddleOCR 기반 다국어 OCR API",
    version="1.0.0"
)

# =====================
# Global Service
# =====================
ocr_service: Optional[PaddleOCRService] = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 PaddleOCR 초기화"""
    global ocr_service
    try:
        ocr_service = PaddleOCRService(
            use_gpu=USE_GPU,
            use_angle_cls=USE_ANGLE_CLS,
            lang=OCR_LANG
        )
        print(f"✅ PaddleOCR initialized (GPU: {USE_GPU}, Lang: {OCR_LANG})")
    except Exception as e:
        print(f"❌ Failed to initialize PaddleOCR: {e}")
        raise

# =====================
# Pydantic Models
# =====================
class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: List[List[int]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    angle: Optional[int] = 0

class OCRResponse(BaseModel):
    status: str
    text_results: List[OCRResult]
    visualization: Optional[str] = None
    total_texts: int
    processing_time: float

# =====================
# Endpoints
# =====================
@app.get("/api/v1/health")
async def health_check():
    """헬스체크"""
    models_loaded = {
        "det": False,
        "rec": False,
        "cls": False
    }

    if ocr_service:
        models_loaded = {
            "det": ocr_service.ocr.text_detector is not None,
            "rec": ocr_service.ocr.text_recognizer is not None,
            "cls": ocr_service.ocr.use_angle_cls
        }

    return {
        "status": "healthy",
        "service": "paddleocr-api",
        "version": "1.0.0",
        "gpu_available": USE_GPU,
        "models_loaded": models_loaded
    }

@app.get("/api/v1/info")
async def get_api_info():
    """API 메타데이터 (BlueprintFlow Auto Discover용)"""
    return {
        "id": "paddleocr",
        "name": "PaddleOCR",
        "display_name": "PaddleOCR",
        "endpoint": "/api/v1/ocr",
        "method": "POST",
        "requires_image": True,

        "inputs": [
            {
                "name": "image",
                "type": "file",
                "required": True,
                "description": "도면 이미지 또는 YOLO 검출 영역"
            }
        ],

        "outputs": [
            {
                "name": "text_results",
                "type": "array",
                "description": "인식된 텍스트 목록 (내용, 위치, 정확도)"
            },
            {
                "name": "visualization",
                "type": "string",
                "description": "OCR 결과 시각화 이미지 (base64)"
            }
        ],

        "parameters": [
            {
                "name": "lang",
                "type": "select",
                "default": "en",
                "options": ["en", "ch", "korean", "japan", "french"],
                "description": "인식 언어"
            },
            {
                "name": "det_db_thresh",
                "type": "number",
                "default": 0.3,
                "min": 0.0,
                "max": 1.0,
                "description": "텍스트 검출 임계값"
            },
            {
                "name": "det_db_box_thresh",
                "type": "number",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "description": "박스 임계값"
            },
            {
                "name": "use_angle_cls",
                "type": "boolean",
                "default": True,
                "description": "회전된 텍스트 감지 여부"
            },
            {
                "name": "min_confidence",
                "type": "number",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "description": "최소 신뢰도"
            },
            {
                "name": "visualize",
                "type": "boolean",
                "default": True,
                "description": "OCR 결과 시각화 이미지 생성"
            }
        ],

        "blueprintflow": {
            "icon": "📄",
            "color": "#06b6d4",
            "category": "api"
        }
    }

@app.post("/api/v1/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    lang: str = Form(default="en"),
    det_db_thresh: float = Form(default=0.3, ge=0.0, le=1.0),
    det_db_box_thresh: float = Form(default=0.5, ge=0.0, le=1.0),
    use_angle_cls: bool = Form(default=True),
    min_confidence: float = Form(default=0.5, ge=0.0, le=1.0),
    visualize: bool = Form(default=True)
):
    """
    OCR 수행 API

    Args:
        file: 이미지 파일
        lang: 인식 언어
        det_db_thresh: 텍스트 검출 임계값
        det_db_box_thresh: 박스 임계값
        use_angle_cls: 회전 감지 여부
        min_confidence: 최소 신뢰도
        visualize: 시각화 여부

    Returns:
        OCRResponse: OCR 결과
    """
    if not ocr_service:
        raise HTTPException(status_code=503, detail="OCR service not initialized")

    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()
        image = load_image(image_bytes)

        # OCR 수행
        results = ocr_service.ocr(
            image,
            det_db_thresh=det_db_thresh,
            det_db_box_thresh=det_db_box_thresh,
            use_angle_cls=use_angle_cls,
            min_confidence=min_confidence
        )

        # 결과 파싱
        text_results = []
        for res in results:
            text_results.append(OCRResult(
                text=res["text"],
                confidence=res["confidence"],
                bbox=res["bbox"],
                angle=res.get("angle", 0)
            ))

        # 시각화
        visualization_base64 = None
        if visualize and len(text_results) > 0:
            vis_image = draw_ocr_results(image, results)
            visualization_base64 = f"data:image/jpeg;base64,{base64.b64encode(vis_image).decode()}"

        processing_time = time.time() - start_time

        return OCRResponse(
            status="success",
            text_results=text_results,
            visualization=visualization_base64,
            total_texts=len(text_results),
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

# =====================
# Main
# =====================
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PADDLEOCR_PORT,
        log_level="info"
    )
```

### 5.2 services/paddleocr_service.py

```python
from paddleocr import PaddleOCR
import numpy as np
from typing import List, Dict, Any

class PaddleOCRService:
    def __init__(
        self,
        use_gpu: bool = True,
        use_angle_cls: bool = True,
        lang: str = "en"
    ):
        """
        PaddleOCR 서비스 초기화

        Args:
            use_gpu: GPU 사용 여부
            use_angle_cls: 회전 감지 사용 여부
            lang: 인식 언어
        """
        self.ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=lang,
            use_gpu=use_gpu,
            show_log=False
        )
        print(f"✅ PaddleOCR loaded (GPU: {use_gpu}, Lang: {lang})")

    def ocr(
        self,
        image: np.ndarray,
        det_db_thresh: float = 0.3,
        det_db_box_thresh: float = 0.5,
        use_angle_cls: bool = True,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        OCR 수행

        Args:
            image: NumPy 이미지 (H, W, C)
            det_db_thresh: 텍스트 검출 임계값
            det_db_box_thresh: 박스 임계값
            use_angle_cls: 회전 감지 여부
            min_confidence: 최소 신뢰도

        Returns:
            List[Dict]: OCR 결과 목록
        """
        # PaddleOCR 실행
        results = self.ocr.ocr(
            image,
            det=True,
            rec=True,
            cls=use_angle_cls
        )

        # 결과 파싱
        ocr_results = []
        if results and results[0]:
            for line in results[0]:
                bbox = line[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                text_info = line[1]  # (text, confidence)

                text = text_info[0]
                confidence = float(text_info[1])

                # 신뢰도 필터링
                if confidence < min_confidence:
                    continue

                ocr_results.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": [[int(x), int(y)] for x, y in bbox],
                    "angle": 0  # PaddleOCR은 각도 직접 제공 안 함
                })

        return ocr_results
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
```

### 5.4 utils/visualization.py

```python
import cv2
import numpy as np
from typing import List, Dict, Any

def draw_ocr_results(
    image: np.ndarray,
    ocr_results: List[Dict[str, Any]],
    thickness: int = 2
) -> bytes:
    """
    OCR 결과를 이미지에 그리기

    Args:
        image: 원본 이미지
        ocr_results: OCR 결과 목록
        thickness: 선 두께

    Returns:
        bytes: JPEG 인코딩된 이미지
    """
    vis_image = image.copy()

    for result in ocr_results:
        bbox = result["bbox"]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        text = result["text"]
        confidence = result["confidence"]

        # 바운딩 박스 (다각형)
        points = np.array(bbox, dtype=np.int32)
        cv2.polylines(vis_image, [points], True, (0, 255, 0), thickness)

        # 레이블 (좌상단)
        label = f"{text} ({confidence:.2f})"
        x1, y1 = bbox[0]
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
  # PaddleOCR API (포트 5006)
  # =====================
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
    # GPU 지원 활성화 ✅
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

networks:
  ax_poc_network:
    driver: bridge
```

### 6.2 네트워크 통신

Gateway API에서 PaddleOCR API 호출 시:

```python
import httpx

async with httpx.AsyncClient() as client:
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
    data = {
        "lang": "en",
        "min_confidence": 0.5,
        "visualize": True
    }

    response = await client.post(
        "http://paddleocr-api:5006/api/v1/ocr",  # ✅ 컨테이너명 사용
        files=files,
        data=data,
        timeout=60.0
    )
```

---

## 7. 테스트 방법

### 7.1 빌드 및 실행

```bash
# 1. 프로젝트 루트로 이동
cd /home/uproot/ax/poc

# 2. PaddleOCR API만 빌드
docker-compose build paddleocr-api

# 3. PaddleOCR API 실행
docker-compose up -d paddleocr-api

# 4. 로그 확인
docker logs paddleocr-api -f
```

**예상 출력**:
```
✅ PaddleOCR loaded (GPU: True, Lang: en)
✅ PaddleOCR initialized (GPU: True, Lang: en)
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:5006
```

### 7.2 헬스체크 테스트

```bash
curl http://localhost:5006/api/v1/health
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

### 7.3 API 메타데이터 테스트

```bash
curl http://localhost:5006/api/v1/info | jq
```

### 7.4 OCR 테스트

```bash
curl -X POST "http://localhost:5006/api/v1/ocr" \
  -F "file=@/path/to/test_drawing.jpg" \
  -F "lang=en" \
  -F "min_confidence=0.5" \
  -F "visualize=true" \
  | jq
```

**예상 응답**:
```json
{
  "status": "success",
  "text_results": [
    {
      "text": "Ø50mm",
      "confidence": 0.92,
      "bbox": [[120, 340], [180, 340], [180, 370], [120, 370]],
      "angle": 0
    }
  ],
  "visualization": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "total_texts": 1,
  "processing_time": 0.45
}
```

### 7.5 BlueprintFlow 통합 테스트

1. **웹 UI 접속**: `http://localhost:5173/blueprintflow/builder`
2. **워크플로우 생성**:
   - ImageInput 노드 + PaddleOCR 노드
   - 연결 및 실행
3. **검증**: OCR 결과 확인

---

## 8. 트러블슈팅

### 8.1 PaddleOCR 모델 다운로드 실패

**증상**:
```
Downloading model from https://...
ConnectionError: ...
```

**해결**:
1. 인터넷 연결 확인
2. 재시도 (첫 실행 시 자동 다운로드)

### 8.2 GPU 인식 안됨

**해결**: YOLO 가이드 참조

### 8.3 한국어 인식 안됨

**증상**: 한글이 깨짐

**해결**:
```python
# lang="korean" 설정
PaddleOCR(lang="korean")
```

---

## 9. 검증 체크리스트

### ✅ 기능 검증

- [ ] `/api/v1/health` 정상 응답
- [ ] `/api/v1/info` 메타데이터 출력
- [ ] `/api/v1/ocr` OCR 수행
- [ ] `visualize=true` 시 시각화 생성
- [ ] GPU 모드 추론 속도 < 2초

### ✅ Docker 통합

- [ ] 빌드 성공
- [ ] 컨테이너 healthy
- [ ] 네트워크 통신 정상

### ✅ BlueprintFlow 통합

- [ ] Auto Discover 인식
- [ ] 대시보드 표시
- [ ] 워크플로우 실행 성공

---

**작성일**: 2025-11-23
**담당자**: 외주 개발자
**예상 작업 시간**: 6시간
