"""
API Specs Router
YAML 스펙 기반 API 메타데이터 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from api_registry import get_api_registry

router = APIRouter(prefix="/api/v1/specs", tags=["specs"])


@router.get("")
async def get_all_specs():
    """
    모든 API 스펙 조회 (YAML 파일 기반)

    Returns:
        모든 API 스펙 목록
    """
    registry = get_api_registry()
    specs = registry.get_all_specs()

    return {
        "status": "success",
        "count": len(specs),
        "specs": specs
    }


@router.get("/resources")
async def get_all_resources():
    """
    모든 API의 리소스 요구사항 조회

    Returns:
        API ID별 리소스 정보 (GPU/CPU 모드, 하이퍼파라미터 영향)
    """
    registry = get_api_registry()
    specs = registry.get_all_specs()

    resources = {}
    for api_id, spec in specs.items():
        if "resources" in spec:
            resources[api_id] = spec["resources"]

    return {
        "status": "success",
        "count": len(resources),
        "resources": resources
    }


@router.get("/{api_id}")
async def get_api_spec(api_id: str):
    """
    특정 API 스펙 조회

    Args:
        api_id: API ID (예: yolo, edocr2, skinmodel)

    Returns:
        API 스펙 (YAML 원본)
    """
    registry = get_api_registry()
    spec = registry.get_spec(api_id)

    if not spec:
        raise HTTPException(status_code=404, detail=f"Spec not found: {api_id}")

    return {
        "status": "success",
        "spec": spec
    }


@router.get("/{api_id}/parameters")
async def get_api_parameters(api_id: str):
    """
    API 파라미터 목록 조회

    Args:
        api_id: API ID

    Returns:
        파라미터 목록
    """
    registry = get_api_registry()
    spec = registry.get_spec(api_id)

    if not spec:
        raise HTTPException(status_code=404, detail=f"Spec not found: {api_id}")

    return {
        "status": "success",
        "api_id": api_id,
        "parameters": spec.get("parameters", [])
    }


@router.get("/{api_id}/blueprintflow")
async def get_blueprintflow_meta(api_id: str):
    """
    BlueprintFlow 노드 메타데이터 조회

    Args:
        api_id: API ID

    Returns:
        BlueprintFlow 노드 정보
    """
    registry = get_api_registry()
    spec = registry.get_spec(api_id)

    if not spec:
        raise HTTPException(status_code=404, detail=f"Spec not found: {api_id}")

    metadata = spec.get("metadata", {})
    server = spec.get("server", {})
    blueprintflow = spec.get("blueprintflow", {})
    i18n = spec.get("i18n", {})

    return {
        "status": "success",
        "node": {
            "id": api_id,
            "type": api_id,
            "label": i18n.get("ko", {}).get("label", metadata.get("name", api_id)),
            "description": i18n.get("ko", {}).get("description", metadata.get("description", "")),
            "category": blueprintflow.get("category", "detection"),
            "color": blueprintflow.get("color", "#6366f1"),
            "icon": blueprintflow.get("icon", "Box"),
            "requiresImage": blueprintflow.get("requiresImage", True),
            "endpoint": server.get("endpoint"),
            "method": server.get("method", "POST"),
            "contentType": server.get("contentType", "multipart/form-data"),
            "inputs": spec.get("inputs", []),
            "outputs": spec.get("outputs", []),
            "parameters": spec.get("parameters", []),
            "mappings": spec.get("mappings", {}),
            "i18n": i18n
        }
    }
