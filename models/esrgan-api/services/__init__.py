"""
ESRGAN Services
"""
from .model import (
    load_model,
    fallback_upscale,
    is_pillow_available,
    is_realesrgan_available,
    get_device,
    PILLOW_AVAILABLE,
    REALESRGAN_AVAILABLE,
    DEVICE
)
from .state import (
    get_upsampler,
    set_upsampler,
    is_model_loaded
)

__all__ = [
    "load_model",
    "fallback_upscale",
    "is_pillow_available",
    "is_realesrgan_available",
    "get_device",
    "PILLOW_AVAILABLE",
    "REALESRGAN_AVAILABLE",
    "DEVICE",
    "get_upsampler",
    "set_upsampler",
    "is_model_loaded",
]
