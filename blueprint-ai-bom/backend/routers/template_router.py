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
    TemplateVersionListResponse,
    TemplateVersion,
    TemplateRollbackRequest,
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


# ============ 버전 관리 엔드포인트 ============

@router.get("/{template_id}/versions", response_model=TemplateVersionListResponse)
async def get_version_history(template_id: str):
    """템플릿 버전 히스토리 조회

    Args:
        template_id: 템플릿 ID

    Returns:
        버전 히스토리 목록 (최신순)
    """
    svc = get_template_svc()
    template = svc.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    versions = svc.get_version_history(template_id)

    return {
        "template_id": template_id,
        "template_name": template.get("name"),
        "current_version": template.get("current_version", len(versions)),
        "versions": [
            {
                "version": v.get("version"),
                "change_summary": v.get("change_summary", ""),
                "node_count": v.get("node_count", 0),
                "edge_count": v.get("edge_count", 0),
                "created_at": v.get("created_at"),
                "created_by": v.get("created_by"),
            }
            for v in versions
        ],
        "total": len(versions)
    }


@router.get("/{template_id}/versions/{version}", response_model=TemplateVersion)
async def get_version(template_id: str, version: int):
    """특정 버전 상세 조회

    Args:
        template_id: 템플릿 ID
        version: 버전 번호

    Returns:
        버전 상세 정보 (노드/엣지 포함)
    """
    svc = get_template_svc()
    version_data = svc.get_version(template_id, version)

    if not version_data:
        raise HTTPException(
            status_code=404,
            detail=f"버전을 찾을 수 없습니다: {template_id} v{version}"
        )

    return version_data


@router.post("/{template_id}/versions")
async def create_version(
    template_id: str,
    change_summary: str = "",
    created_by: Optional[str] = None
):
    """현재 상태로 버전 생성

    Args:
        template_id: 템플릿 ID
        change_summary: 변경 요약
        created_by: 변경자

    Returns:
        생성된 버전 정보
    """
    svc = get_template_svc()
    template = svc.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    version_data = svc._create_version_snapshot(
        template_id,
        change_summary=change_summary or "수동 버전 생성",
        created_by=created_by
    )

    return {
        "success": True,
        "version": version_data.get("version"),
        "message": f"버전 {version_data.get('version')} 생성 완료"
    }


@router.post("/{template_id}/rollback", response_model=TemplateResponse)
async def rollback_template(
    template_id: str,
    request: TemplateRollbackRequest,
    created_by: Optional[str] = None
):
    """특정 버전으로 롤백

    Args:
        template_id: 템플릿 ID
        request: 롤백 요청 (target_version)
        created_by: 변경자

    Returns:
        롤백된 템플릿 정보
    """
    svc = get_template_svc()
    result = svc.rollback_to_version(
        template_id,
        request.target_version,
        created_by=created_by
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"롤백 실패: 버전 {request.target_version}을 찾을 수 없습니다"
        )

    return svc.get_template_summary(template_id)


@router.get("/{template_id}/versions/compare")
async def compare_versions(
    template_id: str,
    version_a: int,
    version_b: int
):
    """두 버전 비교

    Args:
        template_id: 템플릿 ID
        version_a: 비교할 버전 A
        version_b: 비교할 버전 B

    Returns:
        버전 간 차이점
    """
    svc = get_template_svc()
    diff = svc.compare_versions(template_id, version_a, version_b)

    if not diff:
        raise HTTPException(
            status_code=404,
            detail=f"버전 비교 실패: {template_id} v{version_a} 또는 v{version_b}를 찾을 수 없습니다"
        )

    return diff


@router.put("/{template_id}/with-version", response_model=TemplateResponse)
async def update_template_with_version(
    template_id: str,
    updates: TemplateUpdate,
    change_summary: str = "",
    created_by: Optional[str] = None
):
    """버전 관리와 함께 템플릿 수정

    수정 전후 상태를 자동으로 버전으로 저장합니다.

    Args:
        template_id: 템플릿 ID
        updates: 수정할 데이터
        change_summary: 변경 요약 (선택, 자동 생성됨)
        created_by: 변경자

    Returns:
        수정된 템플릿 정보
    """
    svc = get_template_svc()
    result = svc.update_template_with_version(
        template_id,
        updates,
        change_summary=change_summary,
        created_by=created_by
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

    return svc.get_template_summary(template_id)
