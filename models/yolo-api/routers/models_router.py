"""
Models Router - Model Registry Management Endpoints
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from services.registry import get_model_registry

logger = logging.getLogger(__name__)

# Configuration
MODELS_DIR = Path('/app/models')

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class ModelInfo(BaseModel):
    """모델 정보 스키마"""
    name: str
    description: str
    best_for: Optional[str] = None
    classes: Optional[int] = None
    file: Optional[str] = None


@router.get("")
async def get_models():
    """
    등록된 모델 목록 조회

    Returns:
        models: 모델 목록 (ID, 이름, 설명, 파일 크기 등)
        default_model: 기본 모델 ID
    """
    model_registry = get_model_registry()
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    models = model_registry.get_models()
    return {
        "models": list(models.values()),
        "default_model": model_registry.get_default_model(),
        "total": len(models)
    }


@router.get("/{model_id}")
async def get_model(model_id: str):
    """특정 모델 정보 조회"""
    model_registry = get_model_registry()
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    models = model_registry.get_models()
    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    return models[model_id]


@router.post("/{model_id}")
async def add_or_update_model(model_id: str, info: ModelInfo):
    """
    모델 등록/수정

    모델 파일(.pt)은 별도로 업로드해야 함
    """
    model_registry = get_model_registry()
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    model_data = info.dict(exclude_none=True)

    if model_registry.get_model(model_id):
        model_registry.update_model(model_id, model_data)
        return {"message": f"Model '{model_id}' updated", "model_id": model_id}
    else:
        model_registry.add_model(model_id, model_data)
        return {"message": f"Model '{model_id}' added", "model_id": model_id}


@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """모델 삭제 (레지스트리에서만 제거, 파일은 유지)"""
    model_registry = get_model_registry()
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    if model_id == model_registry.get_default_model():
        raise HTTPException(status_code=400, detail="Cannot delete default model")

    if model_registry.delete_model(model_id):
        return {"message": f"Model '{model_id}' deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")


@router.post("/{model_id}/upload")
async def upload_model_file(
    model_id: str,
    file: UploadFile = File(..., description="YOLO 모델 파일 (.pt)")
):
    """모델 파일 업로드"""
    model_registry = get_model_registry()
    if model_registry is None:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="Only .pt files are allowed")

    # 파일 저장
    file_path = MODELS_DIR / f"{model_id}.pt"
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)

    # 레지스트리에 파일 경로 업데이트
    if model_registry.get_model(model_id):
        model_registry.update_model(model_id, {"file": f"{model_id}.pt"})
    else:
        model_registry.add_model(model_id, {"file": f"{model_id}.pt", "name": model_id})

    # 캐시 무효화 (다음 요청시 새 모델 로드)
    if model_id in model_registry._model_cache:
        del model_registry._model_cache[model_id]

    file_size_mb = len(content) / 1024 / 1024
    return {
        "message": f"Model file uploaded: {file.filename}",
        "model_id": model_id,
        "file_size_mb": round(file_size_mb, 2)
    }
