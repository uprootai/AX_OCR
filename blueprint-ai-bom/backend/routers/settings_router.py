"""설정 라우터

API Key 관리, 환경설정 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from services.api_key_service import APIKeyService, APIProvider

router = APIRouter(prefix="/settings", tags=["Settings"])

# 서비스 인스턴스
api_key_service = APIKeyService()


# ============================================================================
# Pydantic 스키마
# ============================================================================

class SetAPIKeyRequest(BaseModel):
    """API 키 설정 요청"""
    provider: str = Field(..., description="API 프로바이더 (openai, anthropic, local, google)")
    api_key: str = Field(..., description="API 키")
    selected_model: Optional[str] = Field(None, description="선택한 모델 ID")


class APIKeyResponse(BaseModel):
    """API 키 응답 (마스킹됨)"""
    provider: str
    has_key: bool
    masked_key: Optional[str]
    selected_model: Optional[str]
    model_info: Optional[Dict[str, Any]]


class TestConnectionRequest(BaseModel):
    """연결 테스트 요청"""
    provider: str
    api_key: Optional[str] = Field(None, description="테스트할 API 키 (없으면 저장된 키 사용)")


class TestConnectionResponse(BaseModel):
    """연결 테스트 응답"""
    success: bool
    provider: str
    model: Optional[str]
    message: str
    latency_ms: Optional[float]


class ProviderModelsResponse(BaseModel):
    """프로바이더별 모델 목록 응답"""
    provider: str
    models: List[Dict[str, Any]]


class AllSettingsResponse(BaseModel):
    """전체 설정 응답"""
    providers: Dict[str, Dict[str, Any]]
    default_provider: Optional[str]


# ============================================================================
# API 엔드포인트
# ============================================================================

@router.get("/api-keys", response_model=AllSettingsResponse)
async def get_all_api_key_settings():
    """모든 프로바이더의 API 키 설정 조회 (마스킹됨)

    Returns:
        프로바이더별 설정 상태
    """
    providers = {}

    for provider in APIProvider:
        settings = api_key_service.get_api_key_settings(provider.value)
        models = api_key_service.get_available_models(provider.value)

        providers[provider.value] = {
            "has_key": settings.get("has_key", False),
            "masked_key": settings.get("masked_key"),
            "selected_model": settings.get("selected_model"),
            "available_models": models,
            "display_name": _get_provider_display_name(provider)
        }

    # 기본 프로바이더 결정
    default_provider = None
    for provider in [APIProvider.OPENAI, APIProvider.ANTHROPIC, APIProvider.GOOGLE, APIProvider.LOCAL]:
        if providers.get(provider.value, {}).get("has_key"):
            default_provider = provider.value
            break

    return AllSettingsResponse(
        providers=providers,
        default_provider=default_provider
    )


@router.get("/api-keys/{provider}", response_model=APIKeyResponse)
async def get_api_key_setting(provider: str):
    """특정 프로바이더의 API 키 설정 조회

    Args:
        provider: API 프로바이더 (openai, anthropic, local, google)

    Returns:
        API 키 설정 (마스킹됨)
    """
    if not _validate_provider(provider):
        raise HTTPException(status_code=400, detail=f"지원하지 않는 프로바이더: {provider}")

    settings = api_key_service.get_api_key_settings(provider)

    # 모델 정보 가져오기
    model_info = None
    if settings.get("selected_model"):
        models = api_key_service.get_available_models(provider)
        for model in models:
            if model["id"] == settings["selected_model"]:
                model_info = model
                break

    return APIKeyResponse(
        provider=provider,
        has_key=settings.get("has_key", False),
        masked_key=settings.get("masked_key"),
        selected_model=settings.get("selected_model"),
        model_info=model_info
    )


@router.post("/api-keys", response_model=Dict[str, Any])
async def set_api_key(request: SetAPIKeyRequest):
    """API 키 설정

    Args:
        request: API 키 설정 요청

    Returns:
        설정 결과
    """
    if not _validate_provider(request.provider):
        raise HTTPException(status_code=400, detail=f"지원하지 않는 프로바이더: {request.provider}")

    # 모델 유효성 검사
    if request.selected_model:
        models = api_key_service.get_available_models(request.provider)
        model_ids = [m["id"] for m in models]
        if request.selected_model not in model_ids:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 모델: {request.selected_model}. 가능한 모델: {model_ids}"
            )

    success = api_key_service.set_api_key(
        provider=request.provider,
        api_key=request.api_key,
        model=request.selected_model
    )

    if not success:
        raise HTTPException(status_code=500, detail="API 키 저장 실패")

    return {
        "success": True,
        "provider": request.provider,
        "message": f"{_get_provider_display_name(APIProvider(request.provider))} API 키가 저장되었습니다."
    }


@router.delete("/api-keys/{provider}", response_model=Dict[str, Any])
async def delete_api_key(provider: str):
    """API 키 삭제

    Args:
        provider: API 프로바이더

    Returns:
        삭제 결과
    """
    if not _validate_provider(provider):
        raise HTTPException(status_code=400, detail=f"지원하지 않는 프로바이더: {provider}")

    success = api_key_service.delete_api_key(provider)

    return {
        "success": success,
        "provider": provider,
        "message": f"{_get_provider_display_name(APIProvider(provider))} API 키가 삭제되었습니다." if success else "삭제할 키가 없습니다."
    }


@router.get("/api-keys/{provider}/models", response_model=ProviderModelsResponse)
async def get_provider_models(provider: str):
    """프로바이더별 사용 가능한 모델 목록 조회

    Args:
        provider: API 프로바이더

    Returns:
        모델 목록
    """
    if not _validate_provider(provider):
        raise HTTPException(status_code=400, detail=f"지원하지 않는 프로바이더: {provider}")

    models = api_key_service.get_available_models(provider)

    return ProviderModelsResponse(
        provider=provider,
        models=models
    )


@router.post("/api-keys/test", response_model=TestConnectionResponse)
async def test_api_connection(request: TestConnectionRequest):
    """API 연결 테스트

    Args:
        request: 테스트 요청

    Returns:
        테스트 결과
    """
    if not _validate_provider(request.provider):
        raise HTTPException(status_code=400, detail=f"지원하지 않는 프로바이더: {request.provider}")

    # 테스트용 API 키 또는 저장된 키 사용
    api_key = request.api_key
    if not api_key:
        stored_key = api_key_service.get_api_key(request.provider)
        if not stored_key:
            return TestConnectionResponse(
                success=False,
                provider=request.provider,
                model=None,
                message="저장된 API 키가 없습니다. API 키를 먼저 설정하거나 테스트할 키를 입력하세요.",
                latency_ms=None
            )
        api_key = stored_key

    # 연결 테스트 실행
    result = api_key_service.test_connection(request.provider, api_key)

    return TestConnectionResponse(
        success=result["success"],
        provider=request.provider,
        model=result.get("model"),
        message=result.get("message", ""),
        latency_ms=result.get("latency_ms")
    )


@router.post("/api-keys/{provider}/model", response_model=Dict[str, Any])
async def set_selected_model(provider: str, model_id: str):
    """선택 모델 변경 (키 변경 없이)

    Args:
        provider: API 프로바이더
        model_id: 선택할 모델 ID

    Returns:
        변경 결과
    """
    if not _validate_provider(provider):
        raise HTTPException(status_code=400, detail=f"지원하지 않는 프로바이더: {provider}")

    # 모델 유효성 검사
    models = api_key_service.get_available_models(provider)
    model_ids = [m["id"] for m in models]
    if model_id not in model_ids:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 모델: {model_id}. 가능한 모델: {model_ids}"
        )

    success = api_key_service.set_selected_model(provider, model_id)

    if not success:
        raise HTTPException(status_code=500, detail="모델 변경 실패")

    return {
        "success": True,
        "provider": provider,
        "model": model_id,
        "message": f"모델이 {model_id}로 변경되었습니다."
    }


@router.get("/providers", response_model=List[Dict[str, Any]])
async def get_all_providers():
    """지원하는 모든 프로바이더 목록

    Returns:
        프로바이더 목록
    """
    providers = []

    for provider in APIProvider:
        settings = api_key_service.get_api_key_settings(provider.value)
        models = api_key_service.get_available_models(provider.value)

        providers.append({
            "id": provider.value,
            "name": _get_provider_display_name(provider),
            "description": _get_provider_description(provider),
            "has_key": settings.get("has_key", False),
            "model_count": len(models),
            "recommended_model": next((m["id"] for m in models if m.get("recommended")), None),
            "requires_internet": provider != APIProvider.LOCAL
        })

    return providers


# ============================================================================
# 헬퍼 함수
# ============================================================================

def _validate_provider(provider: str) -> bool:
    """프로바이더 유효성 검사"""
    try:
        APIProvider(provider)
        return True
    except ValueError:
        return False


def _get_provider_display_name(provider: APIProvider) -> str:
    """프로바이더 표시 이름"""
    names = {
        APIProvider.OPENAI: "OpenAI",
        APIProvider.ANTHROPIC: "Anthropic",
        APIProvider.LOCAL: "로컬 VL API",
        APIProvider.GOOGLE: "Google AI"
    }
    return names.get(provider, provider.value)


def _get_provider_description(provider: APIProvider) -> str:
    """프로바이더 설명"""
    descriptions = {
        APIProvider.OPENAI: "GPT-4 Vision, GPT-4o 등 OpenAI 비전 모델",
        APIProvider.ANTHROPIC: "Claude 3 시리즈 비전 모델",
        APIProvider.LOCAL: "로컬에 설치된 VL API (API 키 불필요)",
        APIProvider.GOOGLE: "Gemini Pro Vision 등 Google AI 모델"
    }
    return descriptions.get(provider, "")
