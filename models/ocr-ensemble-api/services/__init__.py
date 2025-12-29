"""
OCR Ensemble Services
"""
from .clients import (
    call_edocr2,
    call_paddleocr,
    call_tesseract,
    call_trocr,
    check_engine_health,
    get_engine_urls,
    EDOCR2_URL,
    PADDLEOCR_URL,
    TESSERACT_URL,
    TROCR_URL
)
from .ensemble import (
    normalize_text,
    calculate_text_similarity,
    merge_results
)

__all__ = [
    "call_edocr2",
    "call_paddleocr",
    "call_tesseract",
    "call_trocr",
    "check_engine_health",
    "get_engine_urls",
    "EDOCR2_URL",
    "PADDLEOCR_URL",
    "TESSERACT_URL",
    "TROCR_URL",
    "normalize_text",
    "calculate_text_similarity",
    "merge_results",
]
