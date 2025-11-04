#!/usr/bin/env python3
"""
YOLOv11 API Server for Engineering Drawing Analysis
포트: 5005
"""
import os
import time
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ultralytics import YOLO
import torch

# =====================
# Configuration
# =====================

YOLO_API_PORT = int(os.getenv('YOLO_API_PORT', '5005'))
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', '/app/models/best.pt')
UPLOAD_DIR = Path('/tmp/yolo-api/uploads')
RESULTS_DIR = Path('/tmp/yolo-api/results')

# 디렉토리 생성
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# =====================
# Models
# =====================

class Detection(BaseModel):
    """단일 검출 결과"""
    class_id: int = Field(..., description="클래스 ID (0-13)")
    class_name: str = Field(..., description="클래스 이름")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    bbox: Dict[str, int] = Field(..., description="바운딩 박스 {x, y, width, height}")
    value: Optional[str] = Field(None, description="검출된 텍스트 값 (OCR 필요)")

class DetectionResponse(BaseModel):
    """검출 API 응답"""
    status: str = Field(default="success")
    file_id: str = Field(..., description="파일 ID")
    detections: List[Detection] = Field(..., description="검출 목록")
    total_detections: int = Field(..., description="총 검출 개수")
    processing_time: float = Field(..., description="처리 시간 (초)")
    model_used: str = Field(..., description="사용된 모델")
    image_size: Dict[str, int] = Field(..., description="이미지 크기")

class DimensionExtraction(BaseModel):
    """치수 추출 결과"""
    dimensions: List[Detection]
    gdt_symbols: List[Detection]
    surface_roughness: List[Detection]
    text_blocks: List[Detection]

class HealthResponse(BaseModel):
    """Health check 응답"""
    status: str = "healthy"
    model_loaded: bool
    model_path: str
    device: str
    gpu_available: bool
    gpu_name: Optional[str] = None

# =====================
# Global Variables
# =====================

app = FastAPI(
    title="YOLOv11 Drawing Analysis API",
    description="공학 도면 치수/GD&T 추출 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 모델 변수
yolo_model: Optional[YOLO] = None
device: str = "cpu"

# 클래스 이름 매핑
CLASS_NAMES = {
    0: 'diameter_dim',
    1: 'linear_dim',
    2: 'radius_dim',
    3: 'angular_dim',
    4: 'chamfer_dim',
    5: 'tolerance_dim',
    6: 'reference_dim',
    7: 'flatness',
    8: 'cylindricity',
    9: 'position',
    10: 'perpendicularity',
    11: 'parallelism',
    12: 'surface_roughness',
    13: 'text_block'
}

# =====================
# Utility Functions
# =====================

def load_model():
    """모델 로드"""
    global yolo_model, device

    # GPU 사용 가능 확인
    if torch.cuda.is_available():
        device = "0"
        print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        print("⚠️  GPU not available, using CPU")

    # 모델 파일 확인
    if not Path(YOLO_MODEL_PATH).exists():
        print(f"⚠️  Model not found at {YOLO_MODEL_PATH}")
        print(f"   Using default YOLOv11n pretrained model for prototype")
        yolo_model = YOLO('yolo11n.pt')  # 기본 모델
    else:
        print(f"📥 Loading model from {YOLO_MODEL_PATH}")
        yolo_model = YOLO(YOLO_MODEL_PATH)

    print(f"✅ Model loaded successfully on {device}")

def yolo_to_detection_format(result, image_shape) -> List[Detection]:
    """
    YOLO 결과를 Detection 포맷으로 변환

    Args:
        result: YOLO detection result
        image_shape: (height, width, channels)

    Returns:
        List[Detection]: 검출 목록
    """
    detections = []
    boxes = result.boxes

    for box in boxes:
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = CLASS_NAMES.get(cls_id, 'unknown')

        # 바운딩 박스 (xyxy 포맷)
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # 픽셀 좌표로 변환
        bbox = {
            'x': int(x1),
            'y': int(y1),
            'width': int(x2 - x1),
            'height': int(y2 - y1)
        }

        detection = Detection(
            class_id=cls_id,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox,
            value=None  # OCR refinement 필요
        )

        detections.append(detection)

    return detections

def draw_detections_on_image(image: np.ndarray, detections: List[Detection]) -> np.ndarray:
    """
    이미지에 검출 결과 그리기

    Args:
        image: numpy array (BGR)
        detections: 검출 목록

    Returns:
        numpy array: 어노테이션된 이미지
    """
    annotated_img = image.copy()

    # 색상 정의 (BGR)
    colors = {
        'dimension': (255, 100, 0),     # Blue
        'gdt': (0, 255, 100),           # Green
        'surface': (0, 165, 255),       # Orange
        'text': (255, 255, 0)           # Cyan
    }

    for det in detections:
        bbox = det.bbox
        x1 = bbox['x']
        y1 = bbox['y']
        x2 = x1 + bbox['width']
        y2 = y1 + bbox['height']

        # 색상 선택
        if det.class_id <= 6:
            color = colors['dimension']
        elif det.class_id <= 11:
            color = colors['gdt']
        elif det.class_id == 12:
            color = colors['surface']
        else:
            color = colors['text']

        # 박스 그리기
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

        # 라벨 그리기
        label = f"{det.class_name} {det.confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )

        cv2.rectangle(
            annotated_img,
            (x1, y1 - label_h - 10),
            (x1 + label_w, y1),
            color,
            -1
        )

        cv2.putText(
            annotated_img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

    return annotated_img

# =====================
# Startup / Shutdown
# =====================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    print("=" * 70)
    print("🚀 YOLOv11 API Server Starting...")
    print("=" * 70)
    load_model()
    print("=" * 70)
    print(f"✅ Server ready on port {YOLO_API_PORT}")
    print("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    print("🛑 Shutting down YOLOv11 API Server...")

# =====================
# API Endpoints
# =====================

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    gpu_name = None
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

    return HealthResponse(
        status="healthy",
        model_loaded=yolo_model is not None,
        model_path=YOLO_MODEL_PATH,
        device=device,
        gpu_available=torch.cuda.is_available(),
        gpu_name=gpu_name
    )

@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(...),
    conf_threshold: float = Form(default=0.25),
    iou_threshold: float = Form(default=0.7),
    imgsz: int = Form(default=1280),
    visualize: bool = Form(default=True)
):
    """
    객체 검출 (모든 클래스)

    Args:
        file: 이미지 파일
        conf_threshold: 신뢰도 임계값 (0-1)
        iou_threshold: NMS IoU 임계값 (0-1)
        imgsz: 입력 이미지 크기
        visualize: 시각화 이미지 생성 여부

    Returns:
        DetectionResponse: 검출 결과
    """
    if yolo_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    try:
        # 파일 저장
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # 이미지 로드
        image = cv2.imread(str(file_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        img_height, img_width = image.shape[:2]

        # YOLO 추론
        results = yolo_model.predict(
            source=str(file_path),
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=imgsz,
            device=device,
            verbose=False
        )

        # 결과 변환
        detections = yolo_to_detection_format(results[0], image.shape)

        # 시각화 이미지 생성
        if visualize and len(detections) > 0:
            annotated_img = draw_detections_on_image(image, detections)
            viz_path = RESULTS_DIR / f"{file_id}_annotated.jpg"
            cv2.imwrite(str(viz_path), annotated_img)

        # JSON 저장
        result_json = {
            'file_id': file_id,
            'detections': [det.dict() for det in detections],
            'total_detections': len(detections),
            'processing_time': time.time() - start_time,
            'model_used': YOLO_MODEL_PATH,
            'image_size': {'width': img_width, 'height': img_height}
        }

        json_path = RESULTS_DIR / f"{file_id}_result.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)

        processing_time = time.time() - start_time

        return DetectionResponse(
            status="success",
            file_id=file_id,
            detections=detections,
            total_detections=len(detections),
            processing_time=processing_time,
            model_used=YOLO_MODEL_PATH,
            image_size={'width': img_width, 'height': img_height}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.post("/api/v1/extract_dimensions")
async def extract_dimensions(
    file: UploadFile = File(...),
    conf_threshold: float = Form(default=0.25),
    imgsz: int = Form(default=1280)
):
    """
    치수 추출 (dimensions, GD&T, surface roughness 분리)

    Args:
        file: 이미지 파일
        conf_threshold: 신뢰도 임계값
        imgsz: 입력 이미지 크기

    Returns:
        DimensionExtraction: 분류된 검출 결과
    """
    # detect API 호출
    detection_result = await detect_objects(
        file=file,
        conf_threshold=conf_threshold,
        imgsz=imgsz,
        visualize=True
    )

    # 클래스별로 분류
    dimensions = [d for d in detection_result.detections if d.class_id <= 6]
    gdt_symbols = [d for d in detection_result.detections if 7 <= d.class_id <= 11]
    surface_roughness = [d for d in detection_result.detections if d.class_id == 12]
    text_blocks = [d for d in detection_result.detections if d.class_id == 13]

    return {
        'status': 'success',
        'file_id': detection_result.file_id,
        'dimensions': dimensions,
        'gdt_symbols': gdt_symbols,
        'surface_roughness': surface_roughness,
        'text_blocks': text_blocks,
        'total_detections': detection_result.total_detections,
        'processing_time': detection_result.processing_time,
        'model_used': detection_result.model_used
    }

@app.get("/api/v1/download/{file_id}")
async def download_result(
    file_id: str,
    result_type: str = "annotated"  # annotated, json
):
    """
    결과 파일 다운로드

    Args:
        file_id: 파일 ID
        result_type: 결과 타입 (annotated, json)

    Returns:
        FileResponse: 파일
    """
    if result_type == "annotated":
        file_path = RESULTS_DIR / f"{file_id}_annotated.jpg"
        media_type = "image/jpeg"
    elif result_type == "json":
        file_path = RESULTS_DIR / f"{file_id}_result.json"
        media_type = "application/json"
    else:
        raise HTTPException(status_code=400, detail="Invalid result_type")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name
    )

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "YOLOv11 Drawing Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "detect": "/api/v1/detect",
            "extract_dimensions": "/api/v1/extract_dimensions",
            "download": "/api/v1/download/{file_id}",
            "docs": "/docs"
        }
    }

# =====================
# Main
# =====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=YOLO_API_PORT,
        reload=False,
        log_level="info"
    )
