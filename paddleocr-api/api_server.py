#!/usr/bin/env python3
"""
PaddleOCR API Server
도면(Engineering Drawing) 텍스트 인식을 위한 PaddleOCR 기반 API 서버
"""
import os
import time
import logging
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import OCRResponse, HealthResponse
from services.ocr import PaddleOCRService
from utils.helpers import image_to_numpy

# =====================
# Configuration
# =====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PADDLEOCR_PORT", "5006"))
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"
USE_ANGLE_CLS = os.getenv("USE_ANGLE_CLS", "true").lower() == "true"
LANG = os.getenv("OCR_LANG", "en")

# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="PaddleOCR API",
    description="도면 텍스트 인식을 위한 PaddleOCR API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OCR service
ocr_service: Optional[PaddleOCRService] = None


# =====================
# Startup / Shutdown
# =====================

@app.on_event("startup")
async def startup_event():
    """Load PaddleOCR model on startup"""
    global ocr_service

    logger.info(f"Starting PaddleOCR API on port {PORT}")
    ocr_service = PaddleOCRService()
    ocr_service.load_model()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down PaddleOCR API Server")


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Supports both /health and /api/v1/health for compatibility
    """
    return HealthResponse(
        status="healthy" if ocr_service is not None and ocr_service.model is not None else "unhealthy",
        service="paddleocr-api",
        version="1.0.0",
        gpu_available=USE_GPU,
        model_loaded=ocr_service is not None and ocr_service.model is not None,
        lang=LANG
    )


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

    Args:
        file: 분석할 이미지 파일
        det_db_thresh: 텍스트 검출 임계값 (낮을수록 더 많이 검출)
        det_db_box_thresh: 박스 임계값 (높을수록 정확한 박스만)
        use_angle_cls: 회전된 텍스트 감지 여부
        min_confidence: 최소 신뢰도 (이 값 이하는 필터링)

    Returns:
        OCRResponse with detection results
    """
    start_time = time.time()

    if ocr_service is None or ocr_service.model is None:
        raise HTTPException(status_code=503, detail="PaddleOCR model not loaded")

    # Form parameter type conversion (multipart/form-data sends all as strings)
    try:
        min_confidence = float(min_confidence) if isinstance(min_confidence, str) else min_confidence
        det_db_thresh = float(det_db_thresh) if isinstance(det_db_thresh, str) else det_db_thresh
        det_db_box_thresh = float(det_db_box_thresh) if isinstance(det_db_box_thresh, str) else det_db_box_thresh
        use_angle_cls = use_angle_cls if isinstance(use_angle_cls, bool) else (use_angle_cls.lower() == 'true' if isinstance(use_angle_cls, str) else bool(use_angle_cls))
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter type: {e}")

    try:
        # Read image
        image_bytes = await file.read()
        logger.info(f"Processing image: {file.filename}, size: {len(image_bytes)} bytes")

        # Convert to numpy array
        img_array = image_to_numpy(image_bytes)
        logger.info(f"Image shape: {img_array.shape}")

        # Run PaddleOCR inference
        detections = ocr_service.predict(img_array, min_confidence=min_confidence)

        processing_time = time.time() - start_time

        logger.info(f"OCR completed: {len(detections)} texts detected in {processing_time:.2f}s")

        # Metadata
        metadata = {
            "filename": file.filename,
            "image_size": list(img_array.shape[:2]),
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PaddleOCR API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "ocr": "/api/v1/ocr",
            "docs": "/docs"
        }
    }


# =====================
# Main
# =====================

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
