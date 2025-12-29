"""
Surya OCR Global State Management
"""
from typing import Optional, Dict, Any

# Global model instances
_surya_ocr: Optional[Dict[str, Any]] = None
_surya_det: Optional[Any] = None
_surya_layout: Optional[Any] = None


def get_surya_ocr() -> Optional[Dict[str, Any]]:
    """Get Surya OCR predictors dict"""
    return _surya_ocr


def set_surya_ocr(ocr: Optional[Dict[str, Any]]):
    """Set Surya OCR predictors dict"""
    global _surya_ocr
    _surya_ocr = ocr


def get_surya_det() -> Optional[Any]:
    """Get Surya detection predictor"""
    return _surya_det


def set_surya_det(det: Optional[Any]):
    """Set Surya detection predictor"""
    global _surya_det
    _surya_det = det


def get_surya_layout() -> Optional[Any]:
    """Get Surya layout predictor"""
    return _surya_layout


def set_surya_layout(layout: Optional[Any]):
    """Set Surya layout predictor"""
    global _surya_layout
    _surya_layout = layout


def is_model_loaded() -> bool:
    """Check if models are loaded"""
    return _surya_ocr is not None
