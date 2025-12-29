"""
TrOCR Services
"""
from .model import (
    load_model,
    is_trocr_available,
    get_device,
    get_model_name,
    set_model_name,
    clear_cuda_cache,
    TROCR_AVAILABLE,
    DEVICE,
    MODEL_MAP,
)
from .state import (
    get_processor,
    get_model,
    set_processor,
    set_model,
    is_model_loaded,
)

__all__ = [
    "load_model",
    "is_trocr_available",
    "get_device",
    "get_model_name",
    "set_model_name",
    "clear_cuda_cache",
    "TROCR_AVAILABLE",
    "DEVICE",
    "MODEL_MAP",
    "get_processor",
    "get_model",
    "set_processor",
    "set_model",
    "is_model_loaded",
]
