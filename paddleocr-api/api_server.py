"""
PaddleOCR API Server
도면(Engineering Drawing) 텍스트 인식을 위한 PaddleOCR 기반 API 서버
"""

import os
import io
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from PIL import Image
import cv2

# PaddleOCR import
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    print("WARNING: PaddleOCR not installed. Install with: pip install paddleocr")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="PaddleOCR API",
    description="도면 텍스트 인식을 위한 PaddleOCR API",
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

# 환경 변수
PORT = int(os.getenv("PADDLEOCR_PORT", "5006"))
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"
USE_ANGLE_CLS = os.getenv("USE_ANGLE_CLS", "true").lower() == "true"
LANG = os.getenv("OCR_LANG", "en")  # en, ch, korean, japan, etc.

# PaddleOCR 모델 초기화 (전역 변수)
ocr_model = None


def init_paddleocr():
    """PaddleOCR 모델 초기화"""
    global ocr_model

    if PaddleOCR is None:
        logger.error("PaddleOCR is not installed!")
        return False

    try:
        logger.info(f"Initializing PaddleOCR with GPU={USE_GPU}, LANG={LANG}, USE_ANGLE_CLS={USE_ANGLE_CLS}")

        # PaddleOCR 3.x uses different parameter names
        ocr_model = PaddleOCR(
            use_textline_orientation=USE_ANGLE_CLS,  # 텍스트 회전 감지
            lang=LANG,  # 언어 설정
            # use_gpu is deprecated in 3.x, GPU is auto-detected
            text_det_thresh=0.3,  # 텍스트 검출 임계값
            text_det_box_thresh=0.5,  # 박스 임계값
            text_recognition_batch_size=6,  # 배치 크기
        )

        logger.info("PaddleOCR model initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR: {e}")
        return False


# Response Models
class TextDetection(BaseModel):
    """텍스트 검출 결과"""
    text: str
    confidence: float
    bbox: List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    position: Dict[str, float]  # {x, y, width, height}


class OCRResponse(BaseModel):
    """OCR 응답"""
    status: str
    processing_time: float
    total_texts: int
    detections: List[TextDetection]
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    service: str
    version: str
    gpu_available: bool
    model_loaded: bool
    lang: str


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 PaddleOCR 모델 로드"""
    logger.info(f"Starting PaddleOCR API on port {PORT}")
    init_paddleocr()


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint / 헬스체크 엔드포인트

    Supports both /health and /api/v1/health for compatibility
    """
    return HealthResponse(
        status="healthy" if ocr_model is not None else "unhealthy",
        service="paddleocr-api",
        version="1.0.0",
        gpu_available=USE_GPU,
        model_loaded=ocr_model is not None,
        lang=LANG
    )


def image_to_numpy(image_bytes: bytes) -> np.ndarray:
    """이미지 바이트를 numpy array로 변환"""
    try:
        # PIL Image로 로드
        image = Image.open(io.BytesIO(image_bytes))

        # RGB로 변환 (RGBA인 경우)
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        # numpy array로 변환
        img_array = np.array(image)

        # BGR로 변환 (OpenCV 형식)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        return img_array

    except Exception as e:
        logger.error(f"Failed to convert image: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")


def bbox_to_position(bbox: List[List[float]]) -> Dict[str, float]:
    """바운딩 박스를 위치 정보로 변환"""
    x_coords = [point[0] for point in bbox]
    y_coords = [point[1] for point in bbox]

    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)

    return {
        "x": x_min,
        "y": y_min,
        "width": x_max - x_min,
        "height": y_max - y_min
    }


@app.post("/api/v1/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(..., description="이미지 파일 (PNG, JPG, etc.)"),
    det_db_thresh: float = Form(default=0.3, description="텍스트 검출 임계값 (0-1)"),
    det_db_box_thresh: float = Form(default=0.5, description="박스 임계값 (0-1)"),
    use_angle_cls: bool = Form(default=True, description="텍스트 회전 감지 사용"),
    min_confidence: float = Form(default=0.5, description="최소 신뢰도 필터 (0-1)")
):
    """
    PaddleOCR을 사용한 텍스트 인식

    - **file**: 분석할 이미지 파일
    - **det_db_thresh**: 텍스트 검출 임계값 (낮을수록 더 많이 검출)
    - **det_db_box_thresh**: 박스 임계값 (높을수록 정확한 박스만)
    - **use_angle_cls**: 회전된 텍스트 감지 여부
    - **min_confidence**: 최소 신뢰도 (이 값 이하는 필터링)
    """
    start_time = time.time()

    if ocr_model is None:
        raise HTTPException(status_code=503, detail="PaddleOCR model not loaded")

    # Form 파라미터 타입 변환 (multipart/form-data는 모두 문자열로 전달됨)
    try:
        min_confidence = float(min_confidence) if isinstance(min_confidence, str) else min_confidence
        det_db_thresh = float(det_db_thresh) if isinstance(det_db_thresh, str) else det_db_thresh
        det_db_box_thresh = float(det_db_box_thresh) if isinstance(det_db_box_thresh, str) else det_db_box_thresh
        use_angle_cls = use_angle_cls if isinstance(use_angle_cls, bool) else (use_angle_cls.lower() == 'true' if isinstance(use_angle_cls, str) else bool(use_angle_cls))
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter type: {e}")

    try:
        # 이미지 읽기
        image_bytes = await file.read()
        logger.info(f"Processing image: {file.filename}, size: {len(image_bytes)} bytes")

        # numpy array로 변환
        img_array = image_to_numpy(image_bytes)
        logger.info(f"Image shape: {img_array.shape}")

        # PaddleOCR 실행
        # NOTE: PaddleOCR 3.x returns list of OCRResult objects (dict-like)
        results = ocr_model.ocr(img_array)

        logger.info(f"PaddleOCR results type: {type(results)}, len: {len(results) if hasattr(results, '__len__') else 'N/A'}")

        # Handle PaddleOCR 3.x OCRResult format
        detections = []

        if results and len(results) > 0:
            # results is a list, typically with one OCRResult per page
            ocr_result = results[0]  # Get first page result

            # OCRResult is a dict-like object with keys: 'rec_texts', 'rec_scores', 'rec_polys'
            if hasattr(ocr_result, 'get'):
                rec_texts = ocr_result.get('rec_texts', [])
                rec_scores = ocr_result.get('rec_scores', [])
                rec_polys = ocr_result.get('rec_polys', ocr_result.get('dt_polys', []))

                logger.info(f"Detected {len(rec_texts)} text regions")

                # Zip together: polys, texts, scores
                for idx, (poly, text, score) in enumerate(zip(rec_polys, rec_texts, rec_scores)):
                    # Convert numpy array to list of [x, y] points
                    if hasattr(poly, 'tolist'):
                        bbox = poly.tolist()
                    else:
                        bbox = poly

                    # Ensure bbox is in correct format [[x1,y1], [x2,y2], ...]
                    if isinstance(bbox, list) and len(bbox) > 0:
                        if not isinstance(bbox[0], list):
                            # Convert from flat array to list of points
                            bbox = [[float(bbox[i]), float(bbox[i+1])] for i in range(0, len(bbox), 2)]

                    # Filter by confidence
                    confidence = float(score)
                    if confidence < min_confidence:
                        continue

                    # Calculate position from bbox
                    position = bbox_to_position(bbox)

                    detection = TextDetection(
                        text=str(text),
                        confidence=confidence,
                        bbox=bbox,
                        position=position
                    )
                    detections.append(detection)
            else:
                logger.warning(f"Unexpected OCRResult format: {type(ocr_result)}")
        else:
            logger.warning("No OCR results returned")

        processing_time = time.time() - start_time

        logger.info(f"OCR completed: {len(detections)} texts detected in {processing_time:.2f}s")

        # 메타데이터
        metadata = {
            "filename": file.filename,
            "image_size": img_array.shape[:2],
            "parameters": {
                "det_db_thresh": det_db_thresh,
                "det_db_box_thresh": det_db_box_thresh,
                "use_angle_cls": use_angle_cls,
                "min_confidence": min_confidence,
                "lang": LANG
            }
        }

        return OCRResponse(
            status="success",
            processing_time=processing_time,
            total_texts=len(detections),
            detections=detections,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting PaddleOCR API server on port {PORT}")
    logger.info(f"GPU enabled: {USE_GPU}")
    logger.info(f"Language: {LANG}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
