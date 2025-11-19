"""
eDOCr2 API Services
"""
from .ocr_processor import EDOCr2Processor, load_models, get_processor

__all__ = ["EDOCr2Processor", "load_models", "get_processor"]
