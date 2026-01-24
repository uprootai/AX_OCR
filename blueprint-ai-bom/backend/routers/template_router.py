"""Template Router - 워크플로우 템플릿 API

Phase 2: 빌더에서 생성한 워크플로우를 템플릿으로 저장
- 템플릿 CRUD
- 템플릿 복제
- 템플릿 목록
"""

import logging
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException

from schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateDetail,
    TemplateListResponse,
)
from services.template_service import get_template_service, TemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


def get_template_svc() -> TemplateService:
    """템플릿 서비스 의존성"""
    data_dir = Path("/app/data")
    return get_template_service(data_dir)


@router.post("", response_model=TemplateResponse)
async def create_template(template: TemplateCreate):
    """템플릿 생성 (빌더에서 호출)

    Args:
        template: 템플릿 생성 데이터 (워크플로우 포함)

    Returns:
        생성된 템플릿 정보
    """
    svc = get_template_svc()
    result = svc.create_template(template)
    return result


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    model_type: Optional[str] = None,
    limit: int = 50
):
    """템플릿 목록 조회

    Args:
        model_type: 모델 타입 필터 (선택)
        limit: 최대 개수

    Returns:
        템플릿 목록 (요약)
    """
    svc = get_template_svc()
    templates = svc.list_templates(model_type=model_type, limit=limit)

    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(template_id: str):
    """템플릿 상세 조회 (워크플로우 포함)

    Args:
        template_id: 템플릿 ID

    Returns:
        템플릿 상세 정보
    """
    svc = get_template_svc()
    template = svc.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    return template


@router.get("/{template_id}/summary", response_model=TemplateResponse)
async def get_template_summary(template_id: str):
    """템플릿 요약 조회 (노드/엣지 제외)

    Args:
        template_id: 템플릿 ID

    Returns:
        템플릿 요약 정보
    """
    svc = get_template_svc()
    template = svc.get_template_summary(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, updates: TemplateUpdate):
    """템플릿 수정

    Args:
        template_id: 템플릿 ID
        updates: 수정할 데이터

    Returns:
        수정된 템플릿 정보
    """
    svc = get_template_svc()
    result = svc.update_template(template_id, updates)

    if not result:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    # 요약 정보 반환
    return svc.get_template_summary(template_id)


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """템플릿 삭제

    Args:
        template_id: 템플릿 ID

    Returns:
        삭제 결과
    """
    svc = get_template_svc()

    # 사용 중인 프로젝트 확인 (경고 용도)
    template = svc.get_template(template_id)
    if template and template.get("usage_count", 0) > 0:
        logger.warning(
            f"템플릿 '{template_id}'이 {template['usage_count']}개 세션에서 사용 중입니다."
        )

    success = svc.delete_template(template_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    return {
        "success": True,
        "message": f"템플릿 '{template_id}' 삭제 완료"
    }


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: str,
    new_name: str
):
    """템플릿 복제

    Args:
        template_id: 원본 템플릿 ID
        new_name: 새 템플릿 이름

    Returns:
        복제된 템플릿 정보
    """
    svc = get_template_svc()
    result = svc.duplicate_template(template_id, new_name)

    if not result:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    return result


@router.get("/{template_id}/preview")
async def preview_template(template_id: str):
    """템플릿 워크플로우 미리보기

    빌더에서 템플릿 불러오기 전 미리보기용

    Args:
        template_id: 템플릿 ID

    Returns:
        워크플로우 노드/엣지 정보
    """
    svc = get_template_svc()
    template = svc.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    return {
        "template_id": template_id,
        "name": template.get("name"),
        "nodes": template.get("nodes", []),
        "edges": template.get("edges", []),
        "node_count": template.get("node_count", 0),
        "edge_count": template.get("edge_count", 0),
        "node_types": template.get("node_types", [])
    }
