"""
EasyOCR Router - OCR Endpoints
"""
import os
import io
import time
import logging

from fastapi import APIRouter, File, UploadFile, Form
from PIL import Image
import numpy as np

from schemas import ProcessResponse
from services import (
    get_easyocr_reader,
    draw_overlay,
    get_use_gpu,
)

logger = logging.getLogger(__name__)

API_PORT = int(os.getenv("EASYOCR_PORT", "5015"))

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "id": "easyocr",
        "name": "EasyOCR",
        "display_name": "EasyOCR",
        "version": "1.0.0",
        "description": "80+ language support, easy to use, CPU/GPU support",
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
            {"name": "image", "type": "Image", "required": True, "description": "Input image"}
        ],
        "outputs": [
            {"name": "texts", "type": "TextResult[]", "description": "Recognized texts"},
            {"name": "full_text", "type": "string", "description": "Full text"}
        ],
        "parameters": [
            {"name": "languages", "type": "string", "default": "ko,en", "description": "Recognition languages (comma separated)"},
            {"name": "detail", "type": "boolean", "default": True, "description": "Detailed results (with bbox)"},
            {"name": "paragraph", "type": "boolean", "default": False, "description": "Combine by paragraph"}
        ]
    }


@router.get("/languages")
async def get_supported_languages():
    """Supported languages list"""
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


@router.post("/ocr", response_model=ProcessResponse)
async def ocr_process(
    file: UploadFile = File(..., description="Input image"),
    languages: str = Form(default="ko,en", description="Recognition languages (comma separated)"),
    detail: bool = Form(default=True, description="Detailed results (with bbox)"),
    paragraph: bool = Form(default=False, description="Combine by paragraph"),
    batch_size: int = Form(default=1, description="Batch size"),
    visualize: bool = Form(default=False, description="Generate overlay image"),
):
    """
    EasyOCR Processing

    - 80+ language support
    - Multi-language simultaneous recognition (English compatible with all languages)
    - CPU/GPU both supported
    - Visualization overlay image
    """
    start_time = time.time()

    try:
        # Parse languages
        lang_list = [l.strip() for l in languages.split(",")]

        # Get reader
        reader = get_easyocr_reader(lang_list, gpu=get_use_gpu())

        # Load image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        logger.info(f"Processing image: {file.filename}, size: {image.size}, languages: {lang_list}")

        # Run OCR
        results = reader.readtext(
            image_np,
            detail=1,  # Always get detailed results
            paragraph=paragraph,
            batch_size=batch_size,
        )

        # Parse results
        texts = []
        full_text_parts = []

        for result in results:
            bbox, text, confidence = result

            # Convert bbox to list
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

        # Generate overlay image
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


@router.post("/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="Input image"),
    languages: str = Form(default="ko,en", description="Recognition languages"),
    detail: bool = Form(default=True, description="Detailed results"),
    paragraph: bool = Form(default=False, description="Paragraph mode"),
    visualize: bool = Form(default=False, description="Generate overlay image"),
):
    """Main processing endpoint (BlueprintFlow compatible)"""
    return await ocr_process(file, languages, detail, paragraph, 1, visualize)
