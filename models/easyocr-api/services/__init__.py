"""
EasyOCR Services
"""
from .model import (
    get_easyocr_reader,
    draw_overlay,
    is_gpu_available,
    get_use_gpu,
    USE_GPU,
)
from .state import (
    get_readers,
    add_reader,
    clear_readers,
    has_reader,
)

__all__ = [
    "get_easyocr_reader",
    "draw_overlay",
    "is_gpu_available",
    "get_use_gpu",
    "USE_GPU",
    "get_readers",
    "add_reader",
    "clear_readers",
    "has_reader",
]
