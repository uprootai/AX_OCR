"""
API Registry Router
자동 검색 시스템 및 API 등록 관리
"""

from fastapi import APIRouter, HTTPException
from api_registry import get_api_registry

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


@router.get("/discover")
async def discover_apis(host: str = "localhost"):
    """
    API 자동 검색

    네트워크에서 /api/v1/info 엔드포인트를 제공하는 API를 자동으로 검색합니다.

    Args:
        host: 검색할 호스트 (기본: localhost)

    Returns:
        발견된 API 목록
    """
    registry = get_api_registry()

    discovered = await registry.discover_apis(host=host)

    return {
        "status": "success",
        "host": host,
        "discovered_count": len(discovered),
        "apis": [api.model_dump() for api in discovered]
    }


@router.get("/list")
async def list_registered_apis():
    """
    등록된 모든 API 목록 조회

    Returns:
        등록된 API 목록 (상태 정보 포함)
    """
    registry = get_api_registry()
    apis = registry.get_all_apis()

    return {
        "status": "success",
        "total_count": len(apis),
        "apis": [api.model_dump() for api in apis]
    }


@router.get("/healthy")
async def get_healthy_apis():
    """
    Healthy 상태인 API만 조회

    Returns:
        Healthy 상태의 API 목록
    """
    registry = get_api_registry()
    apis = registry.get_healthy_apis()

    return {
        "status": "success",
        "count": len(apis),
        "apis": [api.model_dump() for api in apis]
    }


@router.get("/category/{category}")
async def get_apis_by_category(category: str):
    """
    카테고리별 API 목록 조회

    Args:
        category: API 카테고리 (detection, ocr, segmentation, prediction 등)

    Returns:
        해당 카테고리의 API 목록
    """
    registry = get_api_registry()
    apis = registry.get_apis_by_category(category)

    return {
        "status": "success",
        "category": category,
        "count": len(apis),
        "apis": [api.model_dump() for api in apis]
    }


@router.post("/health-check")
async def trigger_health_check():
    """
    모든 등록된 API의 헬스체크 즉시 실행

    Returns:
        헬스체크 결과
    """
    registry = get_api_registry()
    await registry.check_all_health()

    apis = registry.get_all_apis()
    healthy_count = len(registry.get_healthy_apis())

    return {
        "status": "success",
        "total_apis": len(apis),
        "healthy_apis": healthy_count,
        "unhealthy_apis": len(apis) - healthy_count,
        "apis": [
            {
                "id": api.id,
                "name": api.display_name,
                "status": api.status,
                "last_check": api.last_check.isoformat() if api.last_check else None
            }
            for api in apis
        ]
    }


@router.get("/{api_id}")
async def get_api_info(api_id: str):
    """
    특정 API 정보 조회

    Args:
        api_id: API ID

    Returns:
        API 메타데이터
    """
    registry = get_api_registry()
    api = registry.get_api(api_id)

    if not api:
        raise HTTPException(status_code=404, detail=f"API not found: {api_id}")

    return {
        "status": "success",
        "api": api.model_dump()
    }


@router.post("/load-specs")
async def load_specs_from_files(host: str = "localhost"):
    """
    YAML 스펙 파일에서 API 레지스트리 로드

    네트워크 검색 없이 로컬 스펙 파일만 사용합니다.

    Args:
        host: API 서버 호스트 (기본: localhost)

    Returns:
        로드된 API 목록
    """
    registry = get_api_registry()
    loaded = registry.load_from_specs(host=host)

    return {
        "status": "success",
        "host": host,
        "loaded_count": len(loaded),
        "apis": [api.model_dump() for api in loaded]
    }
