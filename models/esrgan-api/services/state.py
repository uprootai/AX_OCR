"""
ESRGAN Global State Management

Manages global model instance for the ESRGAN API.
"""
from typing import Optional, Any

# Global model instance
_upsampler: Optional[Any] = None


def get_upsampler() -> Optional[Any]:
    """Get global upsampler instance"""
    return _upsampler


def set_upsampler(upsampler: Optional[Any]):
    """Set global upsampler instance (called from lifespan)"""
    global _upsampler
    _upsampler = upsampler


def is_model_loaded() -> bool:
    """Check if model is loaded"""
    return _upsampler is not None
