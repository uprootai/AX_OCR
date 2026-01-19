"""
eDOCr2 API Services
"""
from .ocr_processor import EDOCr2Processor, load_models, get_processor
from .svg_generator import generate_ocr_svg, ocr_to_svg_data

__all__ = [
    "EDOCr2Processor",
    "load_models",
    "get_processor",
    "generate_ocr_svg",
    "ocr_to_svg_data",
]
