"""
EasyOCR API Server
80+ 언어 지원, 간편 사용, CPU/GPU 지원

포트: 5015
GitHub: https://github.com/JaidedAI/EasyOCR
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
import numpy as np

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("EASYOCR_PORT", "5015"))
USE_GPU = os.getenv("EASYOCR_GPU", "true").lower() == "true"

# EasyOCR reader (lazy loading)
easyocr_readers = {}


def get_easyocr_reader(languages: List[str], gpu: bool = True):
    """EasyOCR Reader 캐싱"""
    import easyocr

    lang_key = "_".join(sorted(languages))
    if lang_key not in easyocr_readers:
        logger.info(f"Loading EasyOCR reader for languages: {languages}, GPU: {gpu}")
        try:
            easyocr_readers[lang_key] = easyocr.Reader(languages, gpu=gpu)
            logger.info(f"EasyOCR reader loaded for: {languages}")
        except Exception as e:
            logger.error(f"Failed to load EasyOCR: {e}")
            raise HTTPException(status_code=500, detail=f"EasyOCR load failed: {e}")

    return easyocr_readers[lang_key]


def draw_overlay(image: Image.Image, texts: List[Dict]) -> str:
    """OCR 결과를 이미지 위에 오버레이하고 base64로 반환"""
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)

    # 색상 설정 (녹색 - EasyOCR 테마 컬러)
    box_color = (34, 197, 94)  # #22c55e
    text_color = (255, 255, 255)

    for text_item in texts:
        bbox = text_item.get("bbox", [])
        text = text_item.get("text", "")
        conf = text_item.get("confidence", 0)

        if bbox and len(bbox) >= 4:
            # EasyOCR bbox는 폴리곤 형태 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            points = [(int(p[0]), int(p[1])) for p in bbox]

            # 폴리곤 그리기
            draw.polygon(points, outline=box_color)

            # 박스 테두리 두껍게
            for i in range(len(points)):
                draw.line([points[i], points[(i+1) % len(points)]], fill=box_color, width=2)

            # 텍스트 라벨 그리기
            label = f"{text[:15]}{'...' if len(text) > 15 else ''} ({conf:.0%})"
            label_y = max(0, min(p[1] for p in points) - 15)
            label_x = min(p[0] for p in points)
            text_bbox = draw.textbbox((label_x, label_y), label)
            draw.rectangle(text_bbox, fill=box_color)
            draw.text((label_x, label_y), label, fill=text_color)

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
    gpu_enabled: Optional[bool] = None


class TextResult(BaseModel):
    text: str
    confidence: float
    bbox: List[List[int]]


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="EasyOCR API",
    description="EasyOCR - 80+ 언어 지원, 간편 사용",
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
    """서버 시작 시 기본 언어 모델 로드"""
    try:
        # 기본 한국어+영어 모델 미리 로드
        get_easyocr_reader(["ko", "en"], gpu=USE_GPU)
    except Exception as e:
        logger.warning(f"Default model pre-loading failed: {e}")


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    gpu_available = False
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except:
        pass

    return HealthResponse(
        status="healthy",
        service="easyocr-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        gpu_available=gpu_available,
        gpu_enabled=USE_GPU
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "easyocr",
        "name": "EasyOCR",
        "display_name": "EasyOCR",
        "version": "1.0.0",
        "description": "80+ 언어 지원, 간편 사용, CPU/GPU 지원",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/ocr",
        "method": "POST",
        "requires_image": True,
        "blueprintflow": {
            "category": "ocr",
            "color": "#f59e0b",
            "icon": "FileSearch"
        },
        "inputs": [
            {"name": "image", "type": "Image", "required": True, "description": "입력 이미지"}
        ],
        "outputs": [
            {"name": "texts", "type": "TextResult[]", "description": "인식된 텍스트"},
            {"name": "full_text", "type": "string", "description": "전체 텍스트"}
        ],
        "parameters": [
            {"name": "languages", "type": "string", "default": "ko,en", "description": "인식 언어 (쉼표 구분)"},
            {"name": "detail", "type": "boolean", "default": True, "description": "상세 결과 (bbox 포함)"},
            {"name": "paragraph", "type": "boolean", "default": False, "description": "문단 단위로 결합"}
        ]
    }


@app.get("/api/v1/languages")
async def get_supported_languages():
    """지원되는 언어 목록"""
    return {
        "languages": {
            "korean": "ko",
            "english": "en",
            "japanese": "ja",
            "chinese_simplified": "ch_sim",
            "chinese_traditional": "ch_tra",
            "german": "de",
            "french": "fr",
            "spanish": "es",
            "italian": "it",
            "portuguese": "pt",
            "russian": "ru",
            "arabic": "ar",
            "thai": "th",
            "vietnamese": "vi",
            "indonesian": "id",
        },
        "note": "Full list: https://www.jaided.ai/easyocr/"
    }


@app.post("/api/v1/ocr", response_model=ProcessResponse)
async def ocr_process(
    file: UploadFile = File(..., description="입력 이미지"),
    languages: str = Form(default="ko,en", description="인식 언어 (쉼표 구분)"),
    detail: bool = Form(default=True, description="상세 결과 (bbox 포함)"),
    paragraph: bool = Form(default=False, description="문단 단위로 결합"),
    batch_size: int = Form(default=1, description="배치 크기"),
    visualize: bool = Form(default=False, description="오버레이 이미지 생성"),
):
    """
    EasyOCR 처리

    - 80+ 언어 지원
    - 다국어 동시 인식 가능 (영어는 모든 언어와 호환)
    - CPU/GPU 모두 지원
    - 시각화 오버레이 이미지
    """
    start_time = time.time()

    try:
        # 언어 파싱
        lang_list = [l.strip() for l in languages.split(",")]

        # Reader 가져오기
        reader = get_easyocr_reader(lang_list, gpu=USE_GPU)

        # 이미지 로드
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        logger.info(f"Processing image: {file.filename}, size: {image.size}, languages: {lang_list}")

        # OCR 실행
        results = reader.readtext(
            image_np,
            detail=1,  # 항상 상세 결과 가져옴
            paragraph=paragraph,
            batch_size=batch_size,
        )

        # 결과 파싱
        texts = []
        full_text_parts = []

        for result in results:
            bbox, text, confidence = result

            # bbox를 리스트로 변환
            bbox_list = [[int(coord) for coord in point] for point in bbox]

            text_data = {
                "text": text,
                "confidence": float(confidence),
                "bbox": bbox_list
            }

            if detail:
                texts.append(text_data)
            else:
                texts.append({"text": text, "confidence": float(confidence)})

            full_text_parts.append(text)

        full_text = " ".join(full_text_parts) if paragraph else "\n".join(full_text_parts)

        # 오버레이 이미지 생성
        overlay_image = None
        if visualize and texts:
            overlay_image = draw_overlay(image, texts)

        processing_time = time.time() - start_time

        result_data = {
            "texts": texts,
            "full_text": full_text,
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
    detail: bool = Form(default=True, description="상세 결과"),
    paragraph: bool = Form(default=False, description="문단 단위"),
    visualize: bool = Form(default=False, description="오버레이 이미지 생성"),
):
    """메인 처리 엔드포인트 (BlueprintFlow 호환)"""
    return await ocr_process(file, languages, detail, paragraph, 1, visualize)


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting EasyOCR API on port {API_PORT}, GPU: {USE_GPU}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
