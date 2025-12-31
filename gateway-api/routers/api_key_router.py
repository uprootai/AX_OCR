"""
API Key Management Router

API 키 설정, 조회, 삭제, 연결 테스트 엔드포인트
분리: admin_router.py (2025-12-31)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

api_key_router = APIRouter(prefix="/admin", tags=["Admin - API Keys"])


# =============================================================================
# Request/Response Models
# =============================================================================

class SetAPIKeyRequest(BaseModel):
    """API 키 설정 요청"""
    provider: str  # openai, anthropic, google, local
    api_key: str
    model: Optional[str] = None


class TestConnectionRequest(BaseModel):
    """API 연결 테스트 요청"""
    provider: str
    api_key: Optional[str] = None  # 없으면 저장된 키로 테스트


class SetModelRequest(BaseModel):
    """모델 설정 요청"""
    model: str


# =============================================================================
# API Endpoints
# =============================================================================

@api_key_router.get("/api-keys")
async def get_all_api_keys():
    """
    모든 API Key 설정 조회 (키는 마스킹됨)

    Returns:
        Dict containing all provider settings with masked keys
    """
    try:
        from services.api_key_service import get_api_key_service
        service = get_api_key_service()
        settings = service.get_all_settings()
        return {"status": "success", "data": settings}
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_key_router.post("/api-keys")
async def set_api_key(request: SetAPIKeyRequest):
    """
    API Key 설정

    Args:
        request: SetAPIKeyRequest with provider, api_key, and optional model

    Returns:
        Success message
    """
    try:
        from services.api_key_service import get_api_key_service
        service = get_api_key_service()
        success = service.set_api_key(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model
        )
        if success:
            return {"status": "success", "message": f"{request.provider} API Key가 저장되었습니다"}
        else:
            raise HTTPException(status_code=400, detail="API Key 저장 실패")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_key_router.delete("/api-keys/{provider}")
async def delete_api_key(provider: str):
    """
    API Key 삭제

    Args:
        provider: Provider name (openai, anthropic, google, local)

    Returns:
        Success or warning message
    """
    try:
        from services.api_key_service import get_api_key_service
        service = get_api_key_service()
        success = service.delete_api_key(provider)
        if success:
            return {"status": "success", "message": f"{provider} API Key가 삭제되었습니다"}
        else:
            return {"status": "warning", "message": "삭제할 키가 없습니다"}
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_key_router.post("/api-keys/test")
async def test_api_connection(request: TestConnectionRequest):
    """
    API 연결 테스트

    Args:
        request: TestConnectionRequest with provider and optional api_key

    Returns:
        Connection test result with success status and optional error
    """
    try:
        from services.api_key_service import get_api_key_service
        service = get_api_key_service()
        result = await service.test_connection(
            provider=request.provider,
            api_key=request.api_key
        )
        return result
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {"success": False, "error": str(e), "provider": request.provider}


@api_key_router.post("/api-keys/{provider}/model")
async def set_api_model(provider: str, request: SetModelRequest):
    """
    Provider의 모델 선택

    Args:
        provider: Provider name
        request: SetModelRequest with model name

    Returns:
        Success message
    """
    try:
        from services.api_key_service import get_api_key_service
        service = get_api_key_service()
        success = service.set_model(provider, request.model)
        if success:
            return {"status": "success", "message": f"{provider} 모델이 {request.model}로 설정되었습니다"}
        else:
            raise HTTPException(status_code=400, detail="모델 설정 실패")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_key_router.get("/api-keys/{provider}")
async def get_api_key_for_service(provider: str):
    """
    특정 Provider의 API Key 조회 (복호화된 평문)

    주의: 내부 서비스 호출용 - 외부 노출 금지

    Args:
        provider: Provider name

    Returns:
        API key and model settings
    """
    try:
        from services.api_key_service import get_api_key_service
        service = get_api_key_service()
        api_key = service.get_api_key(provider)
        model = service.get_model(provider)

        if api_key:
            return {
                "status": "success",
                "api_key": api_key,
                "model": model
            }
        else:
            return {
                "status": "not_found",
                "api_key": None,
                "model": model
            }
    except Exception as e:
        logger.error(f"Failed to get API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))
