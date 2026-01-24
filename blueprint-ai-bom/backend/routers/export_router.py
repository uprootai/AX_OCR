"""Export Router - 세션 Export API

Phase 2E: 검증 완료된 세션을 패키지로 내보내기
Phase 2F: Self-contained Export (Docker 이미지 포함)
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from schemas.export import (
    ExportPreview,
    ExportRequest,
    ExportResponse,
    ExportHistoryResponse,
    SelfContainedExportRequest,
    SelfContainedExportResponse,
    SelfContainedPreview,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])

# 의존성 주입용 전역 변수
_session_service = None
_export_service = None
_template_service = None
_project_service = None


def set_export_services(session_service, export_service, template_service=None, project_service=None):
    """서비스 인스턴스 설정"""
    global _session_service, _export_service, _template_service, _project_service
    _session_service = session_service
    _export_service = export_service
    _template_service = template_service
    _project_service = project_service


def get_services():
    """서비스 의존성 조회"""
    if _session_service is None or _export_service is None:
        raise HTTPException(status_code=500, detail="Export service not initialized")
    return {
        "session": _session_service,
        "export": _export_service,
        "template": _template_service,
        "project": _project_service,
    }


# =============================================================================
# Self-contained Export (Docker 이미지 포함)
# NOTE: 이 엔드포인트들은 /{filename} 패턴보다 먼저 정의되어야 함
# =============================================================================


@router.get(
    "/sessions/{session_id}/self-contained/preview",
    response_model=SelfContainedPreview
)
async def get_self_contained_preview(
    session_id: str,
    port_offset: int = 10000,
):
    """Self-contained Export 미리보기

    포함될 Docker 서비스 목록과 예상 크기, 포트 매핑 정보를 미리 확인합니다.

    Args:
        session_id: 세션 ID
        port_offset: 포트 오프셋 (기본값: 10000, 예: 5005 → 15005)

    Returns:
        SelfContainedPreview: Self-contained Export 미리보기 정보
    """
    services = get_services()

    session = services["session"].get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")

    # 템플릿 정보 조회
    template = None
    if services["template"] and session.get("template_id"):
        template = services["template"].get_template(session["template_id"])

    preview = services["export"].get_self_contained_preview(
        session, template, port_offset
    )
    return preview


@router.post(
    "/sessions/{session_id}/self-contained",
    response_model=SelfContainedExportResponse
)
async def create_self_contained_export(
    session_id: str,
    request: SelfContainedExportRequest = SelfContainedExportRequest(),
):
    """Self-contained Export 패키지 생성

    Docker 이미지와 docker-compose.yml을 포함한 완전한 배포 패키지를 생성합니다.
    새로운 환경에서 `./scripts/import.sh` 실행만으로 즉시 사용 가능합니다.

    포트 오프셋을 적용하여 기존 서비스와 충돌 없이 Import된 서비스 확인이 가능합니다.
    예: yolo-api:5005 → imported-yolo-api:15005

    Args:
        session_id: 세션 ID
        request: Self-contained Export 옵션
            - include_images: 세션 이미지 포함 여부 (기본: True)
            - include_docker: Docker 이미지 포함 여부 (기본: True)
            - compress_images: Docker 이미지 gzip 압축 (기본: True)
            - port_offset: 포트 오프셋 (기본: 10000)
            - container_prefix: 컨테이너 접두사 (기본: "imported")

    Returns:
        SelfContainedExportResponse: Export 결과 (포함된 서비스 목록, 포트 매핑 등)
    """
    services = get_services()

    session = services["session"].get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")

    # 템플릿 정보 조회
    template = None
    if services["template"] and session.get("template_id"):
        template = services["template"].get_template(session["template_id"])

    # 프로젝트 정보 조회
    project = None
    if services["project"] and session.get("project_id"):
        project = services["project"].get_project(session["project_id"])

    # Self-contained 패키지 생성
    result = services["export"].create_self_contained_package(
        session=session,
        request=request,
        template=template,
        project=project,
    )

    return result


@router.get("/sessions/{session_id}/self-contained/download/{filename}")
async def download_self_contained_file(session_id: str, filename: str):
    """Self-contained Export 파일 다운로드

    Args:
        session_id: 세션 ID
        filename: 파일명

    Returns:
        FileResponse: ZIP 파일 다운로드
    """
    services = get_services()

    file_path = services["export"].get_export_file(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/zip",
    )


# =============================================================================
# 기본 Export (Phase 2E)
# =============================================================================


@router.get("/sessions/{session_id}/preview", response_model=ExportPreview)
async def get_export_preview(session_id: str):
    """Export 미리보기

    세션의 Export 가능 여부와 포함될 내용을 미리 확인합니다.

    Args:
        session_id: 세션 ID

    Returns:
        ExportPreview: Export 미리보기 정보
    """
    services = get_services()

    session = services["session"].get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")

    # 템플릿 정보 조회
    template = None
    if services["template"] and session.get("template_id"):
        template = services["template"].get_template(session["template_id"])

    preview = services["export"].get_export_preview(session, template)
    return preview


@router.post("/sessions/{session_id}", response_model=ExportResponse)
async def create_export_package(
    session_id: str,
    request: ExportRequest = ExportRequest(),
):
    """Export 패키지 생성

    검증 완료된 세션을 ZIP 패키지로 내보냅니다.

    Args:
        session_id: 세션 ID
        request: Export 옵션

    Returns:
        ExportResponse: Export 결과
    """
    services = get_services()

    session = services["session"].get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")

    # Export 가능 여부 확인
    preview = services["export"].get_export_preview(session)
    if not preview.can_export:
        raise HTTPException(
            status_code=400,
            detail=f"Export할 수 없습니다: {preview.reason}"
        )

    # 템플릿 정보 조회
    template = None
    if services["template"] and session.get("template_id"):
        template = services["template"].get_template(session["template_id"])

    # 프로젝트 정보 조회
    project = None
    if services["project"] and session.get("project_id"):
        project = services["project"].get_project(session["project_id"])

    # Export 패키지 생성
    result = services["export"].create_export_package(
        session=session,
        request=request,
        template=template,
        project=project,
    )

    return result


@router.get("/sessions/{session_id}/download/{filename}")
async def download_export_file(session_id: str, filename: str):
    """Export 파일 다운로드

    Args:
        session_id: 세션 ID
        filename: 파일명

    Returns:
        FileResponse: ZIP 파일 다운로드
    """
    services = get_services()

    file_path = services["export"].get_export_file(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/zip",
    )


@router.get("/sessions/{session_id}/history", response_model=ExportHistoryResponse)
async def get_export_history(session_id: str):
    """Export 이력 조회

    Args:
        session_id: 세션 ID

    Returns:
        ExportHistoryResponse: Export 이력
    """
    services = get_services()

    session = services["session"].get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")

    exports = services["export"].list_exports(session_id)

    return ExportHistoryResponse(
        session_id=session_id,
        exports=exports,
        total=len(exports),
    )


# NOTE: 이 엔드포인트는 /{filename} 와일드카드 패턴이므로 가장 마지막에 정의
@router.delete("/sessions/{session_id}/{filename}")
async def delete_export_file(session_id: str, filename: str):
    """Export 파일 삭제

    Args:
        session_id: 세션 ID
        filename: 파일명

    Returns:
        삭제 결과
    """
    services = get_services()

    success = services["export"].delete_export(filename)
    if not success:
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")

    return {
        "success": True,
        "session_id": session_id,
        "filename": filename,
        "message": "Export 파일이 삭제되었습니다."
    }
