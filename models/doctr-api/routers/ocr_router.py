"""
DocTR Router - OCR Endpoints
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
    load_doctr_model,
    draw_overlay,
    get_doctr_model,
)

logger = logging.getLogger(__name__)

API_PORT = int(os.getenv("DOCTR_PORT", "5014"))

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "id": "doctr",
        "name": "DocTR",
        "display_name": "DocTR",
        "version": "1.0.0",
        "description": "Document Text Recognition - 2-stage pipeline",
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
            {"name": "image", "type": "Image", "required": True, "description": "Input image or PDF"}
        ],
        "outputs": [
            {"name": "texts", "type": "WordResult[]", "description": "Recognized words"},
            {"name": "full_text", "type": "string", "description": "Full text"},
            {"name": "blocks", "type": "BlockResult[]", "description": "Text blocks"}
        ],
        "parameters": [
            {"name": "det_arch", "type": "string", "default": "db_resnet50", "description": "Detection architecture"},
            {"name": "reco_arch", "type": "string", "default": "crnn_vgg16_bn", "description": "Recognition architecture"},
            {"name": "straighten_pages", "type": "boolean", "default": False, "description": "Page straightening"}
        ]
    }


@router.post("/ocr", response_model=ProcessResponse)
async def ocr_process(
    file: UploadFile = File(..., description="Input image or PDF"),
    straighten_pages: bool = Form(default=False, description="Page straightening"),
    export_as_xml: bool = Form(default=False, description="XML format output"),
    visualize: bool = Form(default=False, description="Generate overlay image"),
):
    """
    DocTR OCR Processing

    - 2-stage pipeline: Detection + Recognition
    - Image and PDF support
    - Strong on structured documents
    - Visualization overlay image
    """
    start_time = time.time()

    try:
        # Ensure model is loaded
        load_doctr_model()
        doctr_model = get_doctr_model()

        # Read file
        file_bytes = await file.read()
        filename = file.filename.lower()

        # Load image (PDF or image)
        pil_image = None  # Store PIL image for overlay
        if filename.endswith('.pdf'):
            doc = doctr_model["DocumentFile"].from_pdf(io.BytesIO(file_bytes))
        else:
            # Convert image to numpy array
            pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            doc = [np.array(pil_image)]

        logger.info(f"Processing document: {file.filename}, pages: {len(doc)}")

        # Run OCR
        result = doctr_model["predictor"](doc)

        # Parse results
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

        # Generate overlay image
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


@router.post("/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="Input image"),
    straighten_pages: bool = Form(default=False, description="Page straightening"),
    visualize: bool = Form(default=False, description="Generate overlay image"),
):
    """Main processing endpoint (BlueprintFlow compatible)"""
    return await ocr_process(file, straighten_pages, False, visualize)
