"""
DSE Bearing Router - API endpoints for DSE Bearing pipeline nodes

실제 OCR 기반 파싱 로직 구현
배럴 파일: 파싱 + 견적/가격/고객 라우터 통합
"""

from fastapi import APIRouter

from .dsebearing_parsing_router import router as parsing_router
from .dsebearing_quote_router import router as quote_router

router = APIRouter(prefix="/api/v1/dsebearing", tags=["DSE Bearing"])
router.include_router(parsing_router)
router.include_router(quote_router)
