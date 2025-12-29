"""
TrOCR Router - OCR Endpoints
"""
import io
import time
import logging
from typing import List

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from schemas import OCRResult, OCRResponse
from services import (
    get_processor,
    get_model,
    set_processor,
    set_model,
    get_device,
    get_model_name,
    set_model_name,
    load_model,
    clear_cuda_cache,
    TROCR_AVAILABLE,
    MODEL_MAP,
)

# Conditional imports
if TROCR_AVAILABLE:
    from PIL import Image
    import torch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "name": "TrOCR",
        "type": "trocr",
        "category": "ocr",
        "description": "Microsoft TrOCR Transformer based OCR - Scene Text Recognition",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "model_type",
                "type": "select",
                "default": "printed",
                "options": ["printed", "handwritten", "large-printed", "large-handwritten"],
                "description": "Model type (printed: print, handwritten: handwriting)"
            },
            {
                "name": "max_length",
                "type": "number",
                "default": 64,
                "min": 16,
                "max": 256,
                "description": "Max output length"
            },
            {
                "name": "num_beams",
                "type": "number",
                "default": 4,
                "min": 1,
                "max": 10,
                "description": "Beam Search beam count (higher = more accurate, slower)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "Input image (cropped text region recommended)"}
        ],
        "outputs": [
            {"name": "texts", "type": "OCRResult[]", "description": "Recognition results"},
            {"name": "full_text", "type": "string", "description": "Full text"}
        ],
        "ensemble_weight": 0.10,
        "notes": "TrOCR is optimized for single text line recognition. For full documents, detect text regions first then process individually."
    }


@router.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    max_length: int = Form(default=64),
    num_beams: int = Form(default=4)
):
    """
    Perform TrOCR

    TrOCR is optimized for single text line images.
    For full documents, use YOLO to detect text regions first.

    Args:
        file: Image file (cropped text line image recommended)
        max_length: Max output length
        num_beams: Beam Search beam count
    """
    start_time = time.time()
    model = get_model()
    processor = get_processor()
    device = get_device()
    model_name = get_model_name()

    if model is None:
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            model=model_name,
            device=device,
            processing_time_ms=0,
            error="TrOCR model not loaded"
        )

    try:
        # Load image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Convert to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Preprocessing
        pixel_values = processor(image, return_tensors="pt").pixel_values.to(device)

        # Inference
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=max_length,
                num_beams=num_beams
            )

        # Decoding
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        processing_time = (time.time() - start_time) * 1000

        # Generate result
        texts = [OCRResult(
            text=generated_text.strip(),
            confidence=0.85  # TrOCR doesn't provide confidence directly
        )]

        logger.info(f"TrOCR complete: '{generated_text[:50]}...', {processing_time:.1f}ms")

        return OCRResponse(
            success=True,
            texts=texts,
            full_text=generated_text.strip(),
            model=model_name,
            device=device,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"TrOCR error: {e}")
        return OCRResponse(
            success=False,
            texts=[],
            full_text="",
            model=model_name,
            device=device,
            processing_time_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


@router.post("/ocr/batch")
async def perform_batch_ocr(
    files: List[UploadFile] = File(...),
    max_length: int = Form(default=64),
    num_beams: int = Form(default=4)
):
    """
    Batch TrOCR - Process multiple text line images at once

    Use when processing text regions detected by YOLO
    """
    model = get_model()
    processor = get_processor()
    device = get_device()
    model_name = get_model_name()

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

        # Batch preprocessing
        pixel_values = processor(images, return_tensors="pt", padding=True).pixel_values.to(device)

        # Batch inference
        with torch.no_grad():
            generated_ids = model.generate(
                pixel_values,
                max_length=max_length,
                num_beams=num_beams
            )

        # Batch decoding
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
            "model": model_name,
            "device": device,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        logger.error(f"TrOCR batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload-model")
async def reload_model_endpoint(model_type: str = Form(default="printed")):
    """
    Reload model (switch to different model type)

    model_type:
    - printed: microsoft/trocr-base-printed (default)
    - handwritten: microsoft/trocr-base-handwritten
    - large-printed: microsoft/trocr-large-printed
    - large-handwritten: microsoft/trocr-large-handwritten
    """
    device = get_device()

    if model_type not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid model_type: {model_type}")

    set_model_name(MODEL_MAP[model_type])

    try:
        # Clear existing model
        set_model(None)
        set_processor(None)
        clear_cuda_cache()

        # Load new model
        processor, model = load_model()

        if model is not None:
            set_processor(processor)
            set_model(model)
            return {"success": True, "model": get_model_name(), "device": device}
        else:
            raise HTTPException(status_code=500, detail="Failed to load model")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
