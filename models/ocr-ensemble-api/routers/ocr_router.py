"""
OCR Router - Ensemble OCR Endpoints
"""
import time
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, Form
import httpx

from schemas import OCRResult, EnsembleResult, EnsembleResponse, HealthResponse
from services import (
    call_edocr2,
    call_paddleocr,
    call_tesseract,
    call_trocr,
    check_engine_health,
    merge_results,
    EDOCR2_URL,
    PADDLEOCR_URL,
    TESSERACT_URL,
    TROCR_URL
)

logger = logging.getLogger(__name__)

# Default weights (from PPT specification)
DEFAULT_WEIGHTS = {
    "edocr2": 0.40,
    "paddleocr": 0.35,
    "tesseract": 0.15,
    "trocr": 0.10
}

router = APIRouter(prefix="/api/v1", tags=["ocr"])


@router.get("/info")
async def get_info():
    """API info (BlueprintFlow metadata)"""
    return {
        "name": "OCR Ensemble",
        "type": "ocr_ensemble",
        "category": "ocr",
        "description": "4-engine OCR ensemble with weighted voting (eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%)",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "edocr2_weight",
                "type": "number",
                "default": 0.40,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "eDOCr2 weight"
            },
            {
                "name": "paddleocr_weight",
                "type": "number",
                "default": 0.35,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "PaddleOCR weight"
            },
            {
                "name": "tesseract_weight",
                "type": "number",
                "default": 0.15,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "Tesseract weight"
            },
            {
                "name": "trocr_weight",
                "type": "number",
                "default": 0.10,
                "min": 0,
                "max": 1,
                "step": 0.05,
                "description": "TrOCR weight"
            },
            {
                "name": "similarity_threshold",
                "type": "number",
                "default": 0.7,
                "min": 0.5,
                "max": 1,
                "step": 0.05,
                "description": "Text similarity threshold for grouping"
            },
            {
                "name": "engines",
                "type": "string",
                "default": "all",
                "description": "Engines to use (comma-separated: edocr2,paddleocr,tesseract,trocr)"
            }
        ],
        "inputs": [
            {"name": "image", "type": "Image", "description": "Input image"}
        ],
        "outputs": [
            {"name": "results", "type": "EnsembleResult[]", "description": "Ensemble results"},
            {"name": "full_text", "type": "string", "description": "Full concatenated text"}
        ],
        "default_weights": DEFAULT_WEIGHTS
    }


@router.post("/ocr", response_model=EnsembleResponse)
async def ensemble_ocr(
    file: UploadFile = File(...),
    edocr2_weight: float = Form(default=0.40),
    paddleocr_weight: float = Form(default=0.35),
    tesseract_weight: float = Form(default=0.15),
    trocr_weight: float = Form(default=0.10),
    similarity_threshold: float = Form(default=0.7),
    engines: str = Form(default="all")
):
    """
    Perform ensemble OCR

    Args:
        file: Image file
        edocr2_weight: eDOCr2 weight (default 0.40)
        paddleocr_weight: PaddleOCR weight (default 0.35)
        tesseract_weight: Tesseract weight (default 0.15)
        trocr_weight: TrOCR weight (default 0.10)
        similarity_threshold: Text similarity threshold
        engines: Engines to use (comma-separated or 'all')
    """
    start_time = time.time()

    # Set weights
    weights = {
        "edocr2": edocr2_weight,
        "paddleocr": paddleocr_weight,
        "tesseract": tesseract_weight,
        "trocr": trocr_weight
    }

    # Determine active engines
    if engines.lower() == "all":
        active_engines = list(weights.keys())
    else:
        active_engines = [e.strip().lower() for e in engines.split(",")]

    # Load image
    image_bytes = await file.read()

    # Call OCR engines in parallel
    engine_results = {}
    engine_status = {}

    async with httpx.AsyncClient() as client:
        tasks = []

        if "edocr2" in active_engines:
            tasks.append(("edocr2", call_edocr2(client, image_bytes)))
        if "paddleocr" in active_engines:
            tasks.append(("paddleocr", call_paddleocr(client, image_bytes)))
        if "tesseract" in active_engines:
            tasks.append(("tesseract", call_tesseract(client, image_bytes)))
        if "trocr" in active_engines:
            tasks.append(("trocr", call_trocr(client, image_bytes)))

        # Parallel execution
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for i, (engine_name, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                engine_results[engine_name] = []
                engine_status[engine_name] = f"error: {str(result)[:50]}"
            else:
                engine_results[engine_name] = result
                engine_status[engine_name] = f"ok ({len(result)} texts)"

    # Merge ensemble results
    ensemble_results = merge_results(engine_results, weights, similarity_threshold)

    # Build full text
    full_text = " ".join([r.text for r in ensemble_results])

    processing_time = (time.time() - start_time) * 1000

    logger.info(
        f"Ensemble OCR complete: {len(ensemble_results)} results, "
        f"engine status: {engine_status}, {processing_time:.1f}ms"
    )

    return EnsembleResponse(
        success=True,
        results=ensemble_results,
        full_text=full_text,
        engine_results={
            k: [OCRResult(**r.model_dump()) for r in v]
            for k, v in engine_results.items()
        },
        engine_status=engine_status,
        weights_used=weights,
        processing_time_ms=processing_time
    )


@router.post("/ocr/compare")
async def compare_engines(
    file: UploadFile = File(...)
):
    """
    Compare all OCR engine results (without ensemble)
    For debugging and performance comparison
    """
    start_time = time.time()
    image_bytes = await file.read()

    results = {}

    async with httpx.AsyncClient() as client:
        # Sequential execution (for timing measurement)
        for engine_name, call_func in [
            ("edocr2", call_edocr2),
            ("paddleocr", call_paddleocr),
            ("tesseract", call_tesseract),
            ("trocr", call_trocr)
        ]:
            engine_start = time.time()
            try:
                texts = await call_func(client, image_bytes)
                results[engine_name] = {
                    "texts": [t.model_dump() for t in texts],
                    "count": len(texts),
                    "time_ms": (time.time() - engine_start) * 1000,
                    "status": "ok"
                }
            except Exception as e:
                results[engine_name] = {
                    "texts": [],
                    "count": 0,
                    "time_ms": (time.time() - engine_start) * 1000,
                    "status": f"error: {str(e)}"
                }

    total_time = (time.time() - start_time) * 1000

    return {
        "engines": results,
        "total_time_ms": total_time
    }


async def health_check_all_engines() -> tuple[str, dict]:
    """Check health of all OCR engines"""
    async with httpx.AsyncClient() as client:
        engines = {
            "edocr2": await check_engine_health(client, EDOCR2_URL, "eDOCr2"),
            "paddleocr": await check_engine_health(client, PADDLEOCR_URL, "PaddleOCR"),
            "tesseract": await check_engine_health(client, TESSERACT_URL, "Tesseract"),
            "trocr": await check_engine_health(client, TROCR_URL, "TrOCR")
        }

    healthy_count = sum(1 for s in engines.values() if s == "healthy")
    status = "healthy" if healthy_count >= 2 else "degraded" if healthy_count >= 1 else "unhealthy"

    return status, engines
