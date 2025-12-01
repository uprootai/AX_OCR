"""
Tesseract OCR API Server
PPT 슬라이드 11 [HOW-2] 멀티 엔진 앙상블의 Tesseract 엔진

eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%
"""
import os
import io
import logging
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Tesseract
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TESSERACT_API_PORT = int(os.getenv("TESSERACT_API_PORT", "5008"))

app = FastAPI(
    title="Tesseract OCR API",
    description="Tesseract 기반 OCR API - 멀티 엔진 앙상블 구성요소",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Schemas
# =====================

class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[int]] = None
    level: Optional[int] = None  # Tesseract output level


class OCRResponse(BaseModel):
    success: bool
    texts: List[OCRResult]
    full_text: str
    language: str
    processing_time_ms: float
    tesseract_version: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    tesseract_available: bool
    tesseract_version: Optional[str] = None
    timestamp: str


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    tesseract_version = None
    if TESSERACT_AVAILABLE:
        try:
            tesseract_version = pytesseract.get_tesseract_version().base_version
        except Exception:
            pass

    return HealthResponse(
        status="healthy" if TESSERACT_AVAILABLE else "degraded",
        service="Tesseract OCR API",
        version="1.0.0",
        tesseract_available=TESSERACT_AVAILABLE,
        tesseract_version=tesseract_version,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "name": "Tesseract OCR",
        "type": "tesseract",
        "category": "ocr",
        "description": "Google Tesseract 기반 OCR 엔진 - 문서 텍스트 인식",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "lang",
                "type": "select",
                "default": "eng",
                "options": ["eng", "kor", "jpn", "chi_sim", "chi_tra", "eng+kor"],
                "description": "인식 언어"
            },
            {
                "name": "psm",
                "type": "select",
                "default": "3",
                "options": ["0", "1", "3", "4", "6", "7", "11", "12", "13"],
                "description": "Page Segmentation Mode (3: 자동, 6: 단일 블록, 11: 희소 텍스트)"
            },
            {
                "name": "oem",
                "type": "select",
                "default": "3",
                "options": ["0", "1", "2", "3"],
                "description": "OCR Engine Mode (0: Legacy, 1: LSTM, 3: 기본)"
            },
            {
                "name": "output_type",
                "type": "select",
                "default": "data",
                "options": ["string", "data", "dict"],
                "description": "출력 형식 (string: 텍스트만, data: 위치정보 포함)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "입력 이미지"}
        ],
        "outputs": [
            {"name": "texts", "type": "OCRResult[]", "description": "인식 결과 목록"},
            {"name": "full_text", "type": "string", "description": "전체 텍스트"}
        ],
        "ensemble_weight": 0.15  # PPT 기준 15%
    }


@app.post("/api/v1/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    lang: str = Form(default="eng"),
    psm: str = Form(default="3"),
    oem: str = Form(default="3"),
    output_type: str = Form(default="data")
):
    """
    Tesseract OCR 수행

    Args:
        file: 이미지 파일
        lang: 언어 코드 (eng, kor, jpn, chi_sim, eng+kor)
        psm: Page Segmentation Mode
        oem: OCR Engine Mode
        output_type: 출력 형식 (string, data, dict)
    """
    import time
    start_time = time.time()

    if not TESSERACT_AVAILABLE:
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            language=lang,
            processing_time_ms=0,
            error="Tesseract is not installed"
        )

    try:
        # 이미지 로드
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # RGB 변환 (필요시)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Tesseract 설정
        custom_config = f"--psm {psm} --oem {oem}"

        texts = []
        full_text = ""

        if output_type == "string":
            # 단순 텍스트 출력
            full_text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            texts = [OCRResult(text=full_text.strip(), confidence=0.9)]

        elif output_type == "data":
            # 위치 정보 포함 출력
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0

                if text and conf > 0:
                    bbox = [
                        data['left'][i],
                        data['top'][i],
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    ]
                    texts.append(OCRResult(
                        text=text,
                        confidence=conf / 100.0,  # 0-100 → 0-1
                        bbox=bbox,
                        level=data['level'][i]
                    ))

            full_text = " ".join([t.text for t in texts])

        else:  # dict
            # 전체 데이터 반환
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
            full_text = pytesseract.image_to_string(image, lang=lang, config=custom_config)

            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    texts.append(OCRResult(
                        text=text,
                        confidence=float(data['conf'][i]) / 100.0 if data['conf'][i] != '-1' else 0,
                        bbox=[data['left'][i], data['top'][i],
                              data['left'][i] + data['width'][i],
                              data['top'][i] + data['height'][i]],
                        level=data['level'][i]
                    ))

        processing_time = (time.time() - start_time) * 1000

        tesseract_version = None
        try:
            tesseract_version = pytesseract.get_tesseract_version().base_version
        except Exception:
            pass

        logger.info(f"Tesseract OCR 완료: {len(texts)}개 텍스트, {processing_time:.1f}ms")

        return OCRResponse(
            success=True,
            texts=texts,
            full_text=full_text.strip(),
            language=lang,
            processing_time_ms=processing_time,
            tesseract_version=tesseract_version
        )

    except Exception as e:
        logger.error(f"Tesseract OCR 오류: {e}")
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            language=lang,
            processing_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


@app.post("/api/v1/ocr/boxes")
async def get_bounding_boxes(
    file: UploadFile = File(...),
    lang: str = Form(default="eng")
):
    """
    텍스트 바운딩 박스만 추출 (YOLO와 유사한 형식)
    """
    if not TESSERACT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tesseract not available")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        if image.mode != "RGB":
            image = image.convert("RGB")

        # 바운딩 박스 추출
        boxes = pytesseract.image_to_boxes(image, lang=lang, output_type=pytesseract.Output.DICT)

        results = []
        h, w = image.size[1], image.size[0]

        for i in range(len(boxes['char'])):
            char = boxes['char'][i]
            # Tesseract boxes는 좌하단 기준이므로 변환
            x1, y1, x2, y2 = boxes['left'][i], h - boxes['top'][i], boxes['right'][i], h - boxes['bottom'][i]
            results.append({
                "char": char,
                "bbox": [x1, min(y1, y2), x2, max(y1, y2)]
            })

        return {
            "success": True,
            "boxes": results,
            "image_size": {"width": w, "height": h}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Tesseract OCR API on port {TESSERACT_API_PORT}")
    logger.info(f"Tesseract available: {TESSERACT_AVAILABLE}")

    if TESSERACT_AVAILABLE:
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.warning(f"Could not get Tesseract version: {e}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=TESSERACT_API_PORT,
        log_level="info"
    )
