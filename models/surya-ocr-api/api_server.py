"""
Surya OCR API Server
90+ 언어 지원, 레이아웃 분석, 테이블 인식

포트: 5013
GitHub: https://github.com/datalab-to/surya
"""
import os
import io
import base64
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from PIL import Image, ImageDraw, ImageFont

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("SURYA_OCR_PORT", "5013"))

# Surya imports (lazy loading)
surya_ocr = None
surya_det = None
surya_layout = None


def load_surya_models():
    """Surya 모델 지연 로딩 (v0.17+ API)"""
    global surya_ocr, surya_det, surya_layout

    if surya_ocr is None:
        logger.info("Loading Surya OCR models...")
        try:
            from surya.foundation import FoundationPredictor
            from surya.recognition import RecognitionPredictor
            from surya.detection import DetectionPredictor

            # Load predictors (new API in v0.17+)
            foundation_predictor = FoundationPredictor()
            det_predictor = DetectionPredictor()
            rec_predictor = RecognitionPredictor(foundation_predictor)

            surya_ocr = {
                "det_predictor": det_predictor,
                "rec_predictor": rec_predictor,
                "foundation_predictor": foundation_predictor,
            }
            surya_det = det_predictor

            # Layout detection (optional)
            try:
                from surya.layout import LayoutPredictor
                surya_layout = LayoutPredictor()
            except Exception as e:
                logger.warning(f"Layout model not available: {e}")
                surya_layout = None

            logger.info("Surya models loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import Surya: {e}")
            raise HTTPException(status_code=500, detail=f"Surya not installed: {e}")


def draw_overlay(image: Image.Image, texts: List[Dict]) -> str:
    """OCR 결과를 이미지 위에 오버레이하고 base64로 반환"""
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)

    # 색상 설정 (보라색 - Surya 테마 컬러)
    box_color = (139, 92, 246)  # #8b5cf6
    text_bg_color = (139, 92, 246, 200)
    text_color = (255, 255, 255)

    for text_item in texts:
        bbox = text_item.get("bbox", [])
        text = text_item.get("text", "")
        conf = text_item.get("confidence", 0)

        if len(bbox) >= 4:
            # bbox 형식: [x1, y1, x2, y2]
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

            # 박스 그리기
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=2)

            # 텍스트 라벨 그리기
            label = f"{text[:20]}{'...' if len(text) > 20 else ''} ({conf:.0%})"
            text_bbox = draw.textbbox((x1, y1 - 15), label)
            draw.rectangle(text_bbox, fill=box_color)
            draw.text((x1, y1 - 15), label, fill=text_color)

    # Base64로 변환
    buffer = io.BytesIO()
    overlay.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    gpu_available: Optional[bool] = None


class TextLine(BaseModel):
    text: str
    confidence: float
    bbox: List[float]


class LayoutElement(BaseModel):
    type: str
    bbox: List[float]
    confidence: float


class OCRResult(BaseModel):
    success: bool
    texts: List[TextLine]
    full_text: str
    layout: Optional[List[LayoutElement]] = None
    language: str
    processing_time: float
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Surya OCR API",
    description="Surya OCR - 90+ 언어 지원, 레이아웃 분석, 테이블 인식",
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
# Startup Event
# =====================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    try:
        load_surya_models()
    except Exception as e:
        logger.warning(f"Model pre-loading failed (will load on first request): {e}")


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    import torch
    return HealthResponse(
        status="healthy",
        service="surya-ocr-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        gpu_available=torch.cuda.is_available()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "surya-ocr",
        "name": "Surya OCR",
        "display_name": "Surya OCR",
        "version": "1.0.0",
        "description": "90+ 언어 지원, 레이아웃 분석, 테이블 인식",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/ocr",
        "method": "POST",
        "requires_image": True,
        "blueprintflow": {
            "category": "ocr",
            "color": "#8b5cf6",
            "icon": "ScanText"
        },
        "inputs": [
            {"name": "image", "type": "Image", "required": True, "description": "입력 이미지"}
        ],
        "outputs": [
            {"name": "texts", "type": "TextLine[]", "description": "인식된 텍스트 라인"},
            {"name": "full_text", "type": "string", "description": "전체 텍스트"},
            {"name": "layout", "type": "LayoutElement[]", "description": "레이아웃 요소"}
        ],
        "parameters": [
            {"name": "languages", "type": "string", "default": "ko,en", "description": "인식 언어 (쉼표 구분)"},
            {"name": "detect_layout", "type": "boolean", "default": False, "description": "레이아웃 분석 활성화"}
        ]
    }


@app.post("/api/v1/ocr", response_model=ProcessResponse)
async def ocr_process(
    file: UploadFile = File(..., description="입력 이미지"),
    languages: str = Form(default="ko,en", description="인식 언어 (쉼표 구분)"),
    detect_layout: bool = Form(default=False, description="레이아웃 분석 활성화"),
    visualize: bool = Form(default=False, description="오버레이 이미지 생성"),
):
    """
    Surya OCR 처리

    - 90+ 언어 텍스트 인식
    - 선택적 레이아웃 분석
    - 시각화 오버레이 이미지
    """
    start_time = time.time()

    try:
        # 모델 로드 확인
        load_surya_models()

        # 이미지 로드
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logger.info(f"Processing image: {file.filename}, size: {image.size}")

        # 언어 파싱
        lang_list = [l.strip() for l in languages.split(",")]

        # OCR 실행 (new v0.17+ API: single call with det_predictor)
        det_predictor = surya_ocr["det_predictor"]
        rec_predictor = surya_ocr["rec_predictor"]

        # Recognition (internally handles detection when det_predictor is provided)
        # task_names should be ['ocr_with_boxes'] for standard OCR
        rec_results = rec_predictor(
            [image],
            task_names=["ocr_with_boxes"],
            det_predictor=det_predictor
        )

        # 결과 파싱
        texts = []
        full_text_parts = []

        if rec_results and len(rec_results) > 0:
            result = rec_results[0]
            for line in result.text_lines:
                text_line = {
                    "text": line.text,
                    "confidence": float(line.confidence) if hasattr(line, 'confidence') else 0.9,
                    "bbox": list(line.bbox) if hasattr(line, 'bbox') else [0, 0, 0, 0]
                }
                texts.append(text_line)
                full_text_parts.append(line.text)

        full_text = "\n".join(full_text_parts)

        # 레이아웃 분석 (선택적)
        layout = None
        if detect_layout and surya_layout is not None:
            try:
                layout_results = surya_layout([image])
                if layout_results and len(layout_results) > 0:
                    layout = []
                    for elem in layout_results[0].bboxes:
                        layout.append({
                            "type": elem.label if hasattr(elem, 'label') else "unknown",
                            "bbox": list(elem.bbox) if hasattr(elem, 'bbox') else [0, 0, 0, 0],
                            "confidence": float(elem.confidence) if hasattr(elem, 'confidence') else 0.9
                        })
            except Exception as e:
                logger.warning(f"Layout detection failed: {e}")

        # 오버레이 이미지 생성
        overlay_image = None
        if visualize and texts:
            overlay_image = draw_overlay(image, texts)

        processing_time = time.time() - start_time

        result_data = {
            "texts": texts,
            "full_text": full_text,
            "layout": layout,
            "languages": lang_list,
            "text_count": len(texts),
        }
        if overlay_image:
            result_data["overlay_image"] = overlay_image

        return ProcessResponse(
            success=True,
            data=result_data,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="입력 이미지"),
    languages: str = Form(default="ko,en", description="인식 언어"),
    detect_layout: bool = Form(default=False, description="레이아웃 분석"),
    visualize: bool = Form(default=False, description="오버레이 이미지 생성"),
):
    """메인 처리 엔드포인트 (BlueprintFlow 호환)"""
    return await ocr_process(file, languages, detect_layout, visualize)


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Surya OCR API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
