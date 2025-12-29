"""
Tesseract OCR Services
"""
# Tesseract
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None
    Image = None


def is_tesseract_available() -> bool:
    return TESSERACT_AVAILABLE


def get_tesseract_version() -> str:
    if TESSERACT_AVAILABLE:
        try:
            return pytesseract.get_tesseract_version().base_version
        except Exception:
            return None
    return None


__all__ = [
    "TESSERACT_AVAILABLE",
    "is_tesseract_available",
    "get_tesseract_version",
    "pytesseract",
    "Image",
]
