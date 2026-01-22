"""
Table Detection and Extraction Router
테이블 검출 및 추출 엔드포인트
"""

import logging
from typing import Optional, List
from datetime import datetime
import io
import base64

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from PIL import Image

from services import detect_tables, extract_table_content, analyze_tables

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Table Detection"])


# =====================
# Request/Response Schemas
# =====================

class TableRegion(BaseModel):
    id: int
    bbox: List[float]
    confidence: float
    label: str


class DetectResponse(BaseModel):
    success: bool
    image_size: dict
    regions: List[TableRegion]
    processing_time_ms: float
    timestamp: str


class TableData(BaseModel):
    id: int
    bbox: Optional[List[float]] = None
    rows: int
    cols: int
    headers: List[str]
    data: List[List]
    html: str


class ExtractResponse(BaseModel):
    success: bool
    tables_count: int
    tables: List[dict]
    processing_time_ms: float
    timestamp: str


class AnalyzeResponse(BaseModel):
    success: bool
    image_size: dict
    regions_detected: int
    tables_extracted: int
    regions: List[dict]
    tables: List[dict]
    processing_time_ms: float
    timestamp: str


# =====================
# Endpoints
# =====================

@router.post("/detect", response_model=DetectResponse)
async def detect_table_regions(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.7)
):
    """
    테이블 영역 검출 (TATR 사용)

    - **file**: 이미지 파일 (PNG, JPG, PDF)
    - **confidence_threshold**: 검출 신뢰도 임계값 (0.0 ~ 1.0)

    Returns:
        검출된 테이블 영역 목록 (bounding boxes)
    """
    import time
    start_time = time.time()

    try:
        # Read and validate image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Detect tables
        regions = detect_tables(image, confidence_threshold)

        processing_time = (time.time() - start_time) * 1000

        return DetectResponse(
            success=True,
            image_size={"width": image.width, "height": image.height},
            regions=[TableRegion(**r) for r in regions],
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ExtractResponse)
async def extract_tables(
    file: UploadFile = File(...),
    ocr_engine: str = Form("tesseract"),
    borderless: bool = Form(True),
    min_confidence: int = Form(50)
):
    """
    테이블 구조 및 내용 추출 (img2table 사용)

    - **file**: 이미지 파일
    - **ocr_engine**: OCR 엔진 선택 (tesseract, paddle, easyocr)
    - **borderless**: 테두리 없는 테이블 검출 여부
    - **min_confidence**: OCR 최소 신뢰도 (0-100)

    Returns:
        추출된 테이블 목록 (headers, data, html)
    """
    import time
    start_time = time.time()

    try:
        # Read and validate image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Extract tables
        tables = extract_table_content(
            image,
            ocr_engine=ocr_engine,
            borderless=borderless,
            min_confidence=min_confidence
        )

        processing_time = (time.time() - start_time) * 1000

        return ExtractResponse(
            success=True,
            tables_count=len(tables),
            tables=tables,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    file: UploadFile = File(...),
    ocr_engine: str = Form("tesseract"),
    borderless: bool = Form(True),
    confidence_threshold: float = Form(0.7),
    min_confidence: int = Form(50)
):
    """
    통합 분석: 테이블 검출 + 구조 추출

    - **file**: 이미지 파일
    - **ocr_engine**: OCR 엔진 선택 (tesseract, paddle, easyocr)
    - **borderless**: 테두리 없는 테이블 검출 여부
    - **confidence_threshold**: 검출 신뢰도 임계값
    - **min_confidence**: OCR 최소 신뢰도

    Returns:
        검출된 영역 + 추출된 테이블 전체 결과
    """
    import time
    start_time = time.time()

    try:
        # Read and validate image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Full analysis
        result = analyze_tables(
            image,
            ocr_engine=ocr_engine,
            borderless=borderless,
            confidence_threshold=confidence_threshold,
            min_confidence=min_confidence
        )

        processing_time = (time.time() - start_time) * 1000

        return AnalyzeResponse(
            success=True,
            image_size=result["image_size"],
            regions_detected=result["regions_detected"],
            tables_extracted=result["tables_extracted"],
            regions=result["regions"],
            tables=result["tables"],
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_info():
    """API 정보 및 지원 옵션"""
    return {
        "service": "Table Detector API",
        "version": "1.0.0",
        "endpoints": {
            "detect": {
                "path": "/api/v1/detect",
                "method": "POST",
                "description": "테이블 영역 검출 (TATR)"
            },
            "extract": {
                "path": "/api/v1/extract",
                "method": "POST",
                "description": "테이블 구조/내용 추출 (img2table)"
            },
            "analyze": {
                "path": "/api/v1/analyze",
                "method": "POST",
                "description": "통합 분석 (검출 + 추출)"
            }
        },
        "supported_ocr_engines": ["tesseract", "paddle", "easyocr"],
        "supported_formats": ["PNG", "JPG", "JPEG", "BMP", "TIFF"],
        "features": {
            "tatr_detection": "Microsoft Table Transformer",
            "structure_extraction": "img2table with OpenCV",
            "borderless_tables": True,
            "multi_table": True
        }
    }
