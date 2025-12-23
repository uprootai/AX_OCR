"""eDOCr2 - Engineering Drawing OCR Package

치수, GD&T, 텍스트 인식을 위한 OCR 패키지.
"""

from . import tools
from . import keras_ocr

__version__ = "2.0.0"
__all__ = ["tools", "keras_ocr"]
