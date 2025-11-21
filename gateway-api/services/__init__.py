"""
Gateway API Services

External API calls and business logic
"""
from .yolo_service import call_yolo_detect
from .ocr_service import call_edocr2_ocr, call_paddleocr
from .segmentation_service import call_edgnet_segment
from .tolerance_service import call_skinmodel_tolerance
from .vl_service import call_vl_api
from .ensemble_service import process_yolo_crop_ocr, ensemble_ocr_results
from .quote_service import calculate_quote

__all__ = [
    # YOLO
    "call_yolo_detect",
    # OCR
    "call_edocr2_ocr",
    "call_paddleocr",
    # Segmentation
    "call_edgnet_segment",
    # Tolerance
    "call_skinmodel_tolerance",
    # VL
    "call_vl_api",
    # Ensemble
    "process_yolo_crop_ocr",
    "ensemble_ocr_results",
    # Quote
    "calculate_quote"
]
