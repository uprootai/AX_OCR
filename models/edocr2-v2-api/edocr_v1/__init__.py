"""
eDOCr v1 Module
Engineering Drawing OCR Service (eDOCr v1 implementation)
"""

from .schemas import (
    OCRRequest,
    EnhancedOCRRequest,
    Dimension,
    GDT,
    TextInfo,
    OCRResult,
    OCRResponse
)
from .utils import (
    convert_to_serializable,
    allowed_file,
    transform_edocr_to_ui_format,
    init_directories,
    UPLOAD_DIR,
    RESULTS_DIR,
    ALLOWED_EXTENSIONS,
    ALPHABET_DIMENSIONS,
    ALPHABET_INFOBLOCK,
    ALPHABET_GDTS
)
from .services import OCRService
from .routers import ocr_router, docs_router

__all__ = [
    # Schemas
    'OCRRequest',
    'EnhancedOCRRequest',
    'Dimension',
    'GDT',
    'TextInfo',
    'OCRResult',
    'OCRResponse',
    # Utils
    'convert_to_serializable',
    'allowed_file',
    'transform_edocr_to_ui_format',
    'init_directories',
    'UPLOAD_DIR',
    'RESULTS_DIR',
    'ALLOWED_EXTENSIONS',
    'ALPHABET_DIMENSIONS',
    'ALPHABET_INFOBLOCK',
    'ALPHABET_GDTS',
    # Services
    'OCRService',
    # Routers
    'ocr_router',
    'docs_router',
]
