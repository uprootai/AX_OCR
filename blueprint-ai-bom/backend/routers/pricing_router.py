"""Pricing Router - 단가 설정 및 GT 관리 API (Phase 4)

프로젝트 단가 설정(pricing_config) CRUD, GT 라벨 업로드/목록
"""

import json
import logging
from typing import List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from schemas.pricing_config import PricingConfig, DEFAULT_PRICING_CONFIG
from services.project_service import get_project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["pricing"])


def get_services():
    """서비스 의존성"""
    data_dir = Path("/app/data")
    return {
        "project_service": get_project_service(data_dir),
    }


# =============================================================================
# 단가 설정 API (Phase 4)
# =============================================================================

@router.get("/{project_id}/pricing-config")
async def get_pricing_config(project_id: str):
    """프로젝트 단가 설정 조회

    현재 단가 설정 반환 (없으면 기본값)

    Args:
        project_id: 프로젝트 ID

    Returns:
        PricingConfig: 단가 설정
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    project_dir = project_service.projects_dir / project_id
    config_file = project_dir / "pricing_config.json"

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PricingConfig(**data)
        except Exception as e:
            logger.warning(f"단가 설정 로드 실패, 기본값 반환: {e}")

    return DEFAULT_PRICING_CONFIG


@router.post("/{project_id}/pricing-config")
async def save_pricing_config(
    project_id: str,
    config: PricingConfig,
):
    """프로젝트 단가 설정 저장

    단가 설정을 pricing_config.json으로 저장합니다.

    Args:
        project_id: 프로젝트 ID
        config: 단가 설정

    Returns:
        저장 결과
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    project_dir = project_service.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    config_file = project_dir / "pricing_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)

    logger.info(f"단가 설정 저장: {project_id} → {config_file}")

    return {
        "project_id": project_id,
        "message": "단가 설정이 저장되었습니다",
        "config": config,
    }


# =============================================================================
# GT 관리 API
# =============================================================================

@router.post("/{project_id}/gt")
async def upload_project_gt(
    project_id: str,
    files: List[UploadFile] = File(...)
):
    """프로젝트 GT 일괄 업로드

    Args:
        project_id: 프로젝트 ID
        files: GT 라벨 파일들 (.txt)

    Returns:
        업로드 결과
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    gt_folder = Path(project.get("gt_folder", ""))
    if not gt_folder.exists():
        gt_folder.mkdir(parents=True, exist_ok=True)

    uploaded = []
    failed = []

    for file in files:
        if not file.filename.endswith(".txt"):
            failed.append(f"{file.filename} (txt 파일만 지원)")
            continue

        try:
            content = await file.read()
            gt_file = gt_folder / file.filename
            with open(gt_file, "wb") as f:
                f.write(content)
            uploaded.append(file.filename)
        except Exception as e:
            failed.append(f"{file.filename} ({str(e)})")

    return {
        "project_id": project_id,
        "uploaded": uploaded,
        "failed": failed,
        "total_uploaded": len(uploaded),
        "total_failed": len(failed)
    }


@router.get("/{project_id}/gt")
async def list_project_gt(project_id: str):
    """프로젝트 GT 목록 조회

    Args:
        project_id: 프로젝트 ID

    Returns:
        GT 파일 목록
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    gt_folder = Path(project.get("gt_folder", ""))
    if not gt_folder.exists():
        return {"project_id": project_id, "gt_files": [], "total": 0}

    gt_files = [f.name for f in gt_folder.glob("*.txt")]

    return {
        "project_id": project_id,
        "gt_files": sorted(gt_files),
        "total": len(gt_files)
    }
