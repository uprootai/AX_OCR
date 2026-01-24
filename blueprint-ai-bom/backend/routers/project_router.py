"""Project Router - 프로젝트 관리 API

Phase 2: 프로젝트 기반 도면 관리
- 프로젝트 CRUD
- 도면 일괄 업로드
- GT/참조도면 관리
"""

import logging
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends

from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetail,
    ProjectListResponse,
    ProjectBatchUploadRequest,
    ProjectBatchUploadResponse,
)
from services.project_service import get_project_service, ProjectService
from services.template_service import get_template_service, TemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


def get_services():
    """서비스 의존성"""
    data_dir = Path("/app/data")
    return {
        "project_service": get_project_service(data_dir),
        "template_service": get_template_service(data_dir),
    }


@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """프로젝트 생성

    Args:
        project: 프로젝트 생성 데이터

    Returns:
        생성된 프로젝트 정보
    """
    services = get_services()
    project_service = services["project_service"]
    template_service = services["template_service"]

    result = project_service.create_project(project)

    # 템플릿 이름 조회
    if result.get("default_template_id"):
        template = template_service.get_template(result["default_template_id"])
        if template:
            result["default_template_name"] = template.get("name")

    return result


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    customer: Optional[str] = None,
    limit: int = 50
):
    """프로젝트 목록 조회

    Args:
        customer: 고객사 필터 (선택)
        limit: 최대 개수

    Returns:
        프로젝트 목록
    """
    services = get_services()
    project_service = services["project_service"]

    projects = project_service.list_projects(customer=customer, limit=limit)

    return {
        "projects": projects,
        "total": len(projects)
    }


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str):
    """프로젝트 상세 조회

    Args:
        project_id: 프로젝트 ID

    Returns:
        프로젝트 상세 정보 (세션 목록 포함)
    """
    services = get_services()
    project_service = services["project_service"]
    template_service = services["template_service"]

    # 세션 서비스는 api_server에서 주입 필요 (순환 참조 방지)
    # 일단 기본 정보만 반환
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # 템플릿 정보 추가
    if project.get("default_template_id"):
        template = template_service.get_template(project["default_template_id"])
        if template:
            project["template"] = template
            project["default_template_name"] = template.get("name")

    # sessions는 api_server에서 별도 처리
    project["sessions"] = []

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, updates: ProjectUpdate):
    """프로젝트 수정

    Args:
        project_id: 프로젝트 ID
        updates: 수정할 데이터

    Returns:
        수정된 프로젝트 정보
    """
    services = get_services()
    project_service = services["project_service"]

    result = project_service.update_project(project_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    return result


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    delete_sessions: bool = False
):
    """프로젝트 삭제

    Args:
        project_id: 프로젝트 ID
        delete_sessions: 세션도 함께 삭제할지 여부

    Returns:
        삭제 결과
    """
    services = get_services()
    project_service = services["project_service"]

    success = project_service.delete_project(
        project_id,
        delete_sessions=delete_sessions,
        session_service=None  # api_server에서 주입 필요
    )

    if not success:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    return {
        "success": True,
        "message": f"프로젝트 '{project_id}' 삭제 완료"
    }


@router.post("/{project_id}/upload-batch", response_model=ProjectBatchUploadResponse)
async def upload_batch(
    project_id: str,
    files: List[UploadFile] = File(...),
    template_id: Optional[str] = Form(None),
    auto_detect: bool = Form(True)
):
    """도면 일괄 업로드

    프로젝트에 여러 도면을 한번에 업로드하고 세션을 생성합니다.

    Args:
        project_id: 프로젝트 ID
        files: 업로드할 도면 파일들
        template_id: 사용할 템플릿 ID (없으면 프로젝트 기본 템플릿)
        auto_detect: 업로드 후 자동 검출 실행 여부

    Returns:
        업로드 결과 (생성된 세션 ID 목록)
    """
    services = get_services()
    project_service = services["project_service"]
    template_service = services["template_service"]

    # 프로젝트 확인
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # 템플릿 결정
    effective_template_id = template_id or project.get("default_template_id")

    # 실제 업로드 및 세션 생성은 api_server에서 처리
    # 여기서는 검증만 수행

    if effective_template_id:
        template = template_service.get_template(effective_template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"템플릿을 찾을 수 없습니다: {effective_template_id}"
            )

    # 파일 검증
    valid_extensions = {".png", ".jpg", ".jpeg", ".pdf", ".tiff", ".tif"}
    failed_files = []

    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in valid_extensions:
            failed_files.append(f"{file.filename} (지원하지 않는 형식)")

    if len(failed_files) == len(files):
        raise HTTPException(
            status_code=400,
            detail=f"업로드 가능한 파일이 없습니다. 지원 형식: {valid_extensions}"
        )

    # 실제 업로드는 api_server에서 처리 (세션 서비스 필요)
    # 여기서는 placeholder 반환
    return {
        "project_id": project_id,
        "uploaded_count": len(files) - len(failed_files),
        "session_ids": [],  # api_server에서 채움
        "failed_files": failed_files,
        "message": "일괄 업로드는 /api/projects/{id}/upload-batch-process 에서 처리됩니다."
    }


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
