"""
TrOCR API Server
Microsoft TrOCR (Transformer-based OCR) - PPT 슬라이드 11 [HOW-2] 멀티 엔진 앙상블

eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%

TrOCR은 Scene Text Recognition에 강점이 있어 도면의 손글씨 스타일 텍스트에 유용
"""
import os
import io
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Hugging Face Transformers
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    from PIL import Image
    import torch
    TROCR_AVAILABLE = True
except ImportError:
    TROCR_AVAILABLE = False
    Image = None
    torch = None

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TROCR_API_PORT = int(os.getenv("TROCR_API_PORT", "5009"))
MODEL_NAME = os.getenv("TROCR_MODEL", "microsoft/trocr-base-printed")
DEVICE = os.getenv("TROCR_DEVICE", "cuda" if torch and torch.cuda.is_available() else "cpu")

# Global model instances
processor = None
model = None

app = FastAPI(
    title="TrOCR API",
    description="Microsoft TrOCR (Transformer OCR) API - 멀티 엔진 앙상블 구성요소",
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


class OCRResponse(BaseModel):
    success: bool
    texts: List[OCRResult]
    full_text: str
    model: str
    device: str
    processing_time_ms: float
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    trocr_available: bool
    model_loaded: bool
    model_name: str
    device: str
    timestamp: str


# =====================
# Model Loading
# =====================

def load_model():
    """TrOCR 모델 로드"""
    global processor, model

    if not TROCR_AVAILABLE:
        logger.warning("TrOCR dependencies not installed")
        return False

    try:
        logger.info(f"Loading TrOCR model: {MODEL_NAME} on {DEVICE}")
        processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
        model.to(DEVICE)
        model.eval()
        logger.info("TrOCR model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load TrOCR model: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    load_model()


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy" if model is not None else "degraded",
        service="TrOCR API",
        version="1.0.0",
        trocr_available=TROCR_AVAILABLE,
        model_loaded=model is not None,
        model_name=MODEL_NAME,
        device=DEVICE,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "name": "TrOCR",
        "type": "trocr",
        "category": "ocr",
        "description": "Microsoft TrOCR Transformer 기반 OCR - Scene Text Recognition",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "model_type",
                "type": "select",
                "default": "printed",
                "options": ["printed", "handwritten", "large-printed", "large-handwritten"],
                "description": "모델 타입 (printed: 인쇄체, handwritten: 필기체)"
            },
            {
                "name": "max_length",
                "type": "number",
                "default": 64,
                "min": 16,
                "max": 256,
                "description": "최대 출력 길이"
            },
            {
                "name": "num_beams",
                "type": "number",
                "default": 4,
                "min": 1,
                "max": 10,
                "description": "Beam Search 빔 수 (높을수록 정확, 느림)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "입력 이미지 (텍스트 영역 크롭 권장)"}
        ],
        "outputs": [
            {"name": "texts", "type": "OCRResult[]", "description": "인식 결과"},
            {"name": "full_text", "type": "string", "description": "전체 텍스트"}
        ],
        "ensemble_weight": 0.10,  # PPT 기준 10%
        "notes": "TrOCR은 단일 텍스트 라인 인식에 최적화됨. 전체 문서는 텍스트 영역 검출 후 개별 처리 권장"
    }


@app.post("/api/v1/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    max_length: int = Form(default=64),
    num_beams: int = Form(default=4)
):
    """
    TrOCR 수행

    TrOCR은 단일 텍스트 라인 이미지에 최적화되어 있음.
    전체 문서 처리 시 YOLO 등으로 텍스트 영역 검출 후 개별 처리 권장.

    Args:
        file: 이미지 파일 (텍스트 라인 크롭 이미지 권장)
        max_length: 최대 출력 길이
        num_beams: Beam Search 빔 수
    """
    start_time = time.time()

    if model is None:
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            model=MODEL_NAME,
            device=DEVICE,
            processing_time_ms=0,
            error="TrOCR model not loaded"
        )

    try:
        # 이미지 로드
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # RGB 변환
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 전처리
        pixel_values = processor(image, return_tensors="pt").pixel_values.to(DEVICE)

        # 추론
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=max_length,
                num_beams=num_beams
            )

        # 디코딩
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        processing_time = (time.time() - start_time) * 1000

        # 결과 생성
        texts = [OCRResult(
            text=generated_text.strip(),
            confidence=0.85  # TrOCR은 confidence를 직접 제공하지 않음
        )]

        logger.info(f"TrOCR 완료: '{generated_text[:50]}...', {processing_time:.1f}ms")

        return OCRResponse(
            success=True,
            texts=texts,
            full_text=generated_text.strip(),
            model=MODEL_NAME,
            device=DEVICE,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"TrOCR 오류: {e}")
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            model=MODEL_NAME,
            device=DEVICE,
            processing_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


@app.post("/api/v1/ocr/batch")
async def perform_batch_ocr(
    files: List[UploadFile] = File(...),
    max_length: int = Form(default=64),
    num_beams: int = Form(default=4)
):
    """
    배치 TrOCR - 여러 텍스트 라인 이미지 동시 처리

    YOLO로 검출한 텍스트 영역들을 한번에 처리할 때 사용
    """
    if model is None:
        raise HTTPException(status_code=503, detail="TrOCR model not loaded")

    start_time = time.time()
    results = []

    try:
        images = []
        for file in files:
            contents = await file.read()
            img = Image.open(io.BytesIO(contents))
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)

        # 배치 전처리
        pixel_values = processor(images, return_tensors="pt", padding=True).pixel_values.to(DEVICE)

        # 배치 추론
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=max_length,
                num_beams=num_beams
            )

        # 배치 디코딩
        generated_texts = processor.batch_decode(generated_ids, skip_special_tokens=True)

        for text in generated_texts:
            results.append({
                "text": text.strip(),
                "confidence": 0.85
            })

        processing_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "model": MODEL_NAME,
            "device": DEVICE,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        logger.error(f"TrOCR 배치 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reload-model")
async def reload_model(model_type: str = Form(default="printed")):
    """
    모델 다시 로드 (다른 모델 타입으로 전환)

    model_type:
    - printed: microsoft/trocr-base-printed (기본)
    - handwritten: microsoft/trocr-base-handwritten
    - large-printed: microsoft/trocr-large-printed
    - large-handwritten: microsoft/trocr-large-handwritten
    """
    global MODEL_NAME, processor, model

    model_map = {
        "printed": "microsoft/trocr-base-printed",
        "handwritten": "microsoft/trocr-base-handwritten",
        "large-printed": "microsoft/trocr-large-printed",
        "large-handwritten": "microsoft/trocr-large-handwritten"
    }

    if model_type not in model_map:
        raise HTTPException(status_code=400, detail=f"Invalid model_type: {model_type}")

    MODEL_NAME = model_map[model_type]

    try:
        # 기존 모델 해제
        model = None
        processor = None
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 새 모델 로드
        success = load_model()

        if success:
            return {"success": True, "model": MODEL_NAME, "device": DEVICE}
        else:
            raise HTTPException(status_code=500, detail="Failed to load model")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting TrOCR API on port {TROCR_API_PORT}")
    logger.info(f"Model: {MODEL_NAME}, Device: {DEVICE}")
    logger.info(f"TrOCR available: {TROCR_AVAILABLE}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=TROCR_API_PORT,
        log_level="info"
    )
