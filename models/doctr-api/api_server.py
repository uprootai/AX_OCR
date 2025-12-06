"""
DocTR API Server
Document Text Recognition - 2단계 파이프라인 (Detection + Recognition)

포트: 5014
GitHub: https://github.com/mindee/doctr
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
API_PORT = int(os.getenv("DOCTR_PORT", "5014"))

# DocTR model (lazy loading)
doctr_model = None


def load_doctr_model():
    """DocTR 모델 지연 로딩"""
    global doctr_model

    if doctr_model is None:
        logger.info("Loading DocTR model...")
        try:
            from doctr.io import DocumentFile
            from doctr.models import ocr_predictor

            # Load pretrained model
            doctr_model = {
                "predictor": ocr_predictor(pretrained=True),
                "DocumentFile": DocumentFile,
            }
            logger.info("DocTR model loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import DocTR: {e}")
            raise HTTPException(status_code=500, detail=f"DocTR not installed: {e}")


def draw_overlay(image: Image.Image, texts: List[Dict]) -> str:
    """OCR 결과를 이미지 위에 오버레이하고 base64로 반환"""
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    width, height = image.size

    # 색상 설정 (청록색 - DocTR 테마 컬러)
    box_color = (14, 165, 233)  # #0ea5e9
    text_color = (255, 255, 255)

    for text_item in texts:
        bbox = text_item.get("bbox", [])
        text = text_item.get("text", "")
        conf = text_item.get("confidence", 0)

        if len(bbox) >= 2:
            # DocTR bbox는 정규화된 값 [[x1,y1], [x2,y2]] 또는 (x1,y1,x2,y2)
            if isinstance(bbox[0], (list, tuple)):
                x1 = int(bbox[0][0] * width)
                y1 = int(bbox[0][1] * height)
                x2 = int(bbox[1][0] * width)
                y2 = int(bbox[1][1] * height)
            else:
                x1 = int(bbox[0] * width)
                y1 = int(bbox[1] * height)
                x2 = int(bbox[2] * width) if len(bbox) > 2 else x1
                y2 = int(bbox[3] * height) if len(bbox) > 3 else y1

            # 박스 그리기
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=2)

            # 텍스트 라벨 그리기
            label = f"{text[:15]}{'...' if len(text) > 15 else ''} ({conf:.0%})"
            label_y = max(0, y1 - 15)
            text_bbox = draw.textbbox((x1, label_y), label)
            draw.rectangle(text_bbox, fill=box_color)
            draw.text((x1, label_y), label, fill=text_color)

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


class WordResult(BaseModel):
    text: str
    confidence: float
    bbox: List[float]


class LineResult(BaseModel):
    text: str
    words: List[WordResult]
    bbox: List[float]


class BlockResult(BaseModel):
    lines: List[LineResult]
    bbox: List[float]


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="DocTR API",
    description="DocTR - Document Text Recognition, 2단계 파이프라인",
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
        load_doctr_model()
    except Exception as e:
        logger.warning(f"Model pre-loading failed (will load on first request): {e}")


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
        service="doctr-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        gpu_available=gpu_available
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "doctr",
        "name": "DocTR",
        "display_name": "DocTR",
        "version": "1.0.0",
        "description": "Document Text Recognition - 2단계 파이프라인",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/ocr",
        "method": "POST",
        "requires_image": True,
        "blueprintflow": {
            "category": "ocr",
            "color": "#10b981",
            "icon": "FileText"
        },
        "inputs": [
            {"name": "image", "type": "Image", "required": True, "description": "입력 이미지 또는 PDF"}
        ],
        "outputs": [
            {"name": "texts", "type": "WordResult[]", "description": "인식된 단어"},
            {"name": "full_text", "type": "string", "description": "전체 텍스트"},
            {"name": "blocks", "type": "BlockResult[]", "description": "텍스트 블록"}
        ],
        "parameters": [
            {"name": "det_arch", "type": "string", "default": "db_resnet50", "description": "Detection 아키텍처"},
            {"name": "reco_arch", "type": "string", "default": "crnn_vgg16_bn", "description": "Recognition 아키텍처"},
            {"name": "straighten_pages", "type": "boolean", "default": False, "description": "페이지 보정"}
        ]
    }


@app.post("/api/v1/ocr", response_model=ProcessResponse)
async def ocr_process(
    file: UploadFile = File(..., description="입력 이미지 또는 PDF"),
    straighten_pages: bool = Form(default=False, description="페이지 보정"),
    export_as_xml: bool = Form(default=False, description="XML 형식 출력"),
    visualize: bool = Form(default=False, description="오버레이 이미지 생성"),
):
    """
    DocTR OCR 처리

    - 2단계 파이프라인: Detection + Recognition
    - 이미지 및 PDF 지원
    - 구조화된 문서에 강함
    - 시각화 오버레이 이미지
    """
    start_time = time.time()

    try:
        # 모델 로드 확인
        load_doctr_model()

        # 파일 읽기
        file_bytes = await file.read()
        filename = file.filename.lower()

        # 이미지 로드 (PDF 또는 이미지)
        pil_image = None  # 오버레이용 PIL 이미지 저장
        if filename.endswith('.pdf'):
            doc = doctr_model["DocumentFile"].from_pdf(io.BytesIO(file_bytes))
        else:
            # 이미지를 numpy array로 변환
            pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            doc = [np.array(pil_image)]

        logger.info(f"Processing document: {file.filename}, pages: {len(doc)}")

        # OCR 실행
        result = doctr_model["predictor"](doc)

        # 결과 파싱
        texts = []
        blocks = []
        full_text_parts = []

        for page in result.pages:
            for block in page.blocks:
                block_lines = []
                block_bbox = list(block.geometry) if hasattr(block, 'geometry') else [0, 0, 1, 1]

                for line in block.lines:
                    line_words = []
                    line_text_parts = []
                    line_bbox = list(line.geometry) if hasattr(line, 'geometry') else [0, 0, 1, 1]

                    for word in line.words:
                        word_data = {
                            "text": word.value,
                            "confidence": float(word.confidence),
                            "bbox": list(word.geometry) if hasattr(word, 'geometry') else [0, 0, 1, 1]
                        }
                        texts.append(word_data)
                        line_words.append(word_data)
                        line_text_parts.append(word.value)

                    line_text = " ".join(line_text_parts)
                    block_lines.append({
                        "text": line_text,
                        "words": line_words,
                        "bbox": line_bbox
                    })
                    full_text_parts.append(line_text)

                blocks.append({
                    "lines": block_lines,
                    "bbox": block_bbox
                })

        full_text = "\n".join(full_text_parts)

        # 오버레이 이미지 생성
        overlay_image = None
        if visualize and texts and pil_image is not None:
            overlay_image = draw_overlay(pil_image, texts)

        processing_time = time.time() - start_time

        result_data = {
            "texts": texts,
            "full_text": full_text,
            "blocks": blocks,
            "word_count": len(texts),
            "block_count": len(blocks),
            "page_count": len(result.pages),
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
    straighten_pages: bool = Form(default=False, description="페이지 보정"),
    visualize: bool = Form(default=False, description="오버레이 이미지 생성"),
):
    """메인 처리 엔드포인트 (BlueprintFlow 호환)"""
    return await ocr_process(file, straighten_pages, False, visualize)


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting DocTR API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
