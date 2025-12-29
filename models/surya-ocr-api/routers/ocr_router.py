"""
Surya OCR Router - OCR Endpoints
"""
import os
import io
import time
import logging

from fastapi import APIRouter, File, UploadFile, Form
from PIL import Image

from schemas import ProcessResponse
from services import (
    load_surya_models,
    draw_overlay,
    get_surya_ocr,
    get_surya_layout,
)

logger = logging.getLogger(__name__)

API_PORT = int(os.getenv("SURYA_OCR_PORT", "5013"))

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "id": "surya-ocr",
        "name": "Surya OCR",
        "display_name": "Surya OCR",
        "version": "1.0.0",
        "description": "90+ language support, layout analysis, table recognition",
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
            {"name": "image", "type": "Image", "required": True, "description": "Input image"}
        ],
        "outputs": [
            {"name": "texts", "type": "TextLine[]", "description": "Recognized text lines"},
            {"name": "full_text", "type": "string", "description": "Full text"},
            {"name": "layout", "type": "LayoutElement[]", "description": "Layout elements"}
        ],
        "parameters": [
            {"name": "languages", "type": "string", "default": "ko,en", "description": "Recognition languages (comma separated)"},
            {"name": "detect_layout", "type": "boolean", "default": False, "description": "Enable layout analysis"}
        ]
    }


@router.post("/ocr", response_model=ProcessResponse)
async def ocr_process(
    file: UploadFile = File(..., description="Input image"),
    languages: str = Form(default="ko,en", description="Recognition languages (comma separated)"),
    detect_layout: bool = Form(default=False, description="Enable layout analysis"),
    visualize: bool = Form(default=False, description="Generate overlay image"),
):
    """
    Surya OCR Processing

    - 90+ language text recognition
    - Optional layout analysis
    - Visualization overlay image
    """
    start_time = time.time()

    try:
        # Ensure models are loaded
        load_surya_models()

        # Load image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logger.info(f"Processing image: {file.filename}, size: {image.size}")

        # Parse languages
        lang_list = [l.strip() for l in languages.split(",")]

        # Get predictors
        surya_ocr = get_surya_ocr()
        surya_layout = get_surya_layout()

        # OCR execution (v0.17+ API)
        det_predictor = surya_ocr["det_predictor"]
        rec_predictor = surya_ocr["rec_predictor"]

        # Recognition
        rec_results = rec_predictor(
            [image],
            task_names=["ocr_with_boxes"],
            det_predictor=det_predictor
        )

        # Parse results
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

        # Layout analysis (optional)
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

        # Generate overlay image
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


@router.post("/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="Input image"),
    languages: str = Form(default="ko,en", description="Recognition languages"),
    detect_layout: bool = Form(default=False, description="Layout analysis"),
    visualize: bool = Form(default=False, description="Generate overlay image"),
):
    """Main processing endpoint (BlueprintFlow compatible)"""
    return await ocr_process(file, languages, detect_layout, visualize)
