"""
eDOCr v1 Routers
API 엔드포인트 레이어
"""

from .ocr_router import router as ocr_router
from .docs_router import router as docs_router

__all__ = ['ocr_router', 'docs_router']
