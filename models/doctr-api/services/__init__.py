"""
DocTR Services
"""
from .model import (
    load_doctr_model,
    draw_overlay,
    is_gpu_available,
)
from .state import (
    get_doctr_model,
    set_doctr_model,
    is_model_loaded,
)

__all__ = [
    "load_doctr_model",
    "draw_overlay",
    "is_gpu_available",
    "get_doctr_model",
    "set_doctr_model",
    "is_model_loaded",
]
