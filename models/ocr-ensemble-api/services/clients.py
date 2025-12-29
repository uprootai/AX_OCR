"""
OCR Engine Clients
HTTP clients for calling individual OCR API services
"""
import os
import logging
from typing import List

import httpx

from schemas import OCRResult

logger = logging.getLogger(__name__)

# OCR Engine URL Configuration
EDOCR2_URL = os.getenv("EDOCR2_URL", "http://edocr2-v2-api:5002")
PADDLEOCR_URL = os.getenv("PADDLEOCR_URL", "http://paddleocr-api:5006")
TESSERACT_URL = os.getenv("TESSERACT_URL", "http://tesseract-api:5008")
TROCR_URL = os.getenv("TROCR_URL", "http://trocr-api:5009")


async def call_edocr2(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """Call eDOCr2 OCR engine"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"language": "eng", "visualize": "false"}

        response = await client.post(
            f"{EDOCR2_URL}/api/v2/ocr",
            files=files,
            data=data,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts") or result.get("text_results") or []
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.8),
                    bbox=t.get("bbox"),
                    source="edocr2"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"eDOCr2 call failed: {e}")
    return []


async def call_paddleocr(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """Call PaddleOCR engine"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"lang": "en", "visualize": "false"}

        response = await client.post(
            f"{PADDLEOCR_URL}/api/v1/ocr",
            files=files,
            data=data,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts") or result.get("results") or []
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.8),
                    bbox=t.get("bbox"),
                    source="paddleocr"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"PaddleOCR call failed: {e}")
    return []


async def call_tesseract(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """Call Tesseract OCR engine"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"lang": "eng", "output_type": "data"}

        response = await client.post(
            f"{TESSERACT_URL}/api/v1/ocr",
            files=files,
            data=data,
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts", [])
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.7),
                    bbox=t.get("bbox"),
                    source="tesseract"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"Tesseract call failed: {e}")
    return []


async def call_trocr(client: httpx.AsyncClient, image_bytes: bytes) -> List[OCRResult]:
    """Call TrOCR engine"""
    try:
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}

        response = await client.post(
            f"{TROCR_URL}/api/v1/ocr",
            files=files,
            timeout=60.0  # TrOCR is slower
        )

        if response.status_code == 200:
            result = response.json()
            texts = result.get("texts", [])
            return [
                OCRResult(
                    text=t.get("text", ""),
                    confidence=t.get("confidence", 0.85),
                    bbox=t.get("bbox"),
                    source="trocr"
                )
                for t in texts if t.get("text")
            ]
    except Exception as e:
        logger.warning(f"TrOCR call failed: {e}")
    return []


async def check_engine_health(client: httpx.AsyncClient, url: str, name: str) -> str:
    """Check OCR engine health status"""
    try:
        # eDOCr2 uses /api/v1/health, others use /health
        health_path = "/api/v1/health" if "edocr2" in name.lower() or "edocr2" in url else "/health"
        response = await client.get(f"{url}{health_path}", timeout=5.0)
        if response.status_code == 200:
            return "healthy"
        return f"unhealthy ({response.status_code})"
    except Exception as e:
        return f"unreachable ({str(e)[:30]})"


def get_engine_urls() -> dict:
    """Get all engine URLs for logging"""
    return {
        "edocr2": EDOCR2_URL,
        "paddleocr": PADDLEOCR_URL,
        "tesseract": TESSERACT_URL,
        "trocr": TROCR_URL
    }
