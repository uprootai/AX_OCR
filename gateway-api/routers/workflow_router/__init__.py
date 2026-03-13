"""
Workflow Router Package
BlueprintFlow 워크플로우 실행 엔드포인트 모음

Barrel re-export: `from routers.workflow_router import router` 호환성 유지
"""

from fastapi import APIRouter

from .core_routes import router as _core_router
from .template_routes import router as _template_router

# 최종 라우터 조합 (기존 prefix/tags 유지)
router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])
router.include_router(_core_router)
router.include_router(_template_router)

__all__ = ["router"]
