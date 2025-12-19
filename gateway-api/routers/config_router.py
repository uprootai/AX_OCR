"""
API Config Router
Custom API 설정 관리
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from blueprintflow.api_config_manager import get_api_config_manager

router = APIRouter(prefix="/api/v1/api-configs", tags=["config"])


@router.get("")
async def get_api_configs():
    """모든 Custom API 설정 조회"""
    manager = get_api_config_manager()
    configs = manager.get_all_configs()

    return {
        "status": "success",
        "configs": list(configs.values()),
        "count": len(configs)
    }


@router.get("/{api_id}")
async def get_api_config(api_id: str):
    """특정 Custom API 설정 조회"""
    manager = get_api_config_manager()
    config = manager.get_config(api_id)

    if not config:
        raise HTTPException(status_code=404, detail=f"API Config not found: {api_id}")

    return {
        "status": "success",
        "config": config
    }


@router.post("")
async def create_api_config(config: Dict[str, Any]):
    """새 Custom API 설정 추가"""
    manager = get_api_config_manager()

    if not config.get("id"):
        raise HTTPException(status_code=400, detail="API Config must have an id")

    success = manager.add_config(config)

    if not success:
        raise HTTPException(status_code=400, detail=f"API Config already exists: {config.get('id')}")

    return {
        "status": "success",
        "message": f"API Config added: {config.get('id')}",
        "config": config
    }


@router.put("/{api_id}")
async def update_api_config(api_id: str, updates: Dict[str, Any]):
    """Custom API 설정 업데이트"""
    manager = get_api_config_manager()

    success = manager.update_config(api_id, updates)

    if not success:
        raise HTTPException(status_code=404, detail=f"API Config not found: {api_id}")

    return {
        "status": "success",
        "message": f"API Config updated: {api_id}"
    }


@router.delete("/{api_id}")
async def delete_api_config(api_id: str):
    """Custom API 설정 삭제"""
    manager = get_api_config_manager()

    success = manager.delete_config(api_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"API Config not found: {api_id}")

    return {
        "status": "success",
        "message": f"API Config deleted: {api_id}"
    }


@router.post("/{api_id}/toggle")
async def toggle_api_config(api_id: str):
    """Custom API 활성화/비활성화 토글"""
    manager = get_api_config_manager()

    success = manager.toggle_enabled(api_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"API Config not found: {api_id}")

    config = manager.get_config(api_id)

    return {
        "status": "success",
        "message": f"API Config toggled: {api_id}",
        "enabled": config.get("enabled", True)
    }
