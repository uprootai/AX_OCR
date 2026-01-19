"""
Services package for PaddleOCR API
"""
from .ocr import PaddleOCRService
from .svg_generator import generate_ocr_svg, ocr_to_svg_data

__all__ = [
    'PaddleOCRService',
    'generate_ocr_svg',
    'ocr_to_svg_data',
]
