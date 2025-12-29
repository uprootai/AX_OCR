"""
TrOCR Global State Management
"""
from typing import Optional, Any

# Global model instances
_processor: Optional[Any] = None
_model: Optional[Any] = None


def get_processor() -> Optional[Any]:
    """Get TrOCR processor instance"""
    return _processor


def get_model() -> Optional[Any]:
    """Get TrOCR model instance"""
    return _model


def set_processor(processor: Optional[Any]):
    """Set TrOCR processor instance"""
    global _processor
    _processor = processor


def set_model(model: Optional[Any]):
    """Set TrOCR model instance"""
    global _model
    _model = model


def is_model_loaded() -> bool:
    """Check if model is loaded"""
    return _model is not None
