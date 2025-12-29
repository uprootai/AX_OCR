"""
Surya OCR Services
"""
from .model import (
    load_surya_models,
    get_korean_font,
    draw_overlay,
    is_gpu_available,
)
from .state import (
    get_surya_ocr,
    set_surya_ocr,
    get_surya_det,
    set_surya_det,
    get_surya_layout,
    set_surya_layout,
    is_model_loaded,
)

__all__ = [
    "load_surya_models",
    "get_korean_font",
    "draw_overlay",
    "is_gpu_available",
    "get_surya_ocr",
    "set_surya_ocr",
    "get_surya_det",
    "set_surya_det",
    "get_surya_layout",
    "set_surya_layout",
    "is_model_loaded",
]
