"""
DocTR Global State Management
"""
from typing import Optional, Dict, Any

# Global model instance
_doctr_model: Optional[Dict[str, Any]] = None


def get_doctr_model() -> Optional[Dict[str, Any]]:
    """Get DocTR model dict"""
    return _doctr_model


def set_doctr_model(model: Optional[Dict[str, Any]]):
    """Set DocTR model dict"""
    global _doctr_model
    _doctr_model = model


def is_model_loaded() -> bool:
    """Check if model is loaded"""
    return _doctr_model is not None
