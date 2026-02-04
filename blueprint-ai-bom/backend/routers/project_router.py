"""Project Router - 프로젝트 관리 API

Phase 2: 프로젝트 기반 도면 관리
- 프로젝트 CRUD
- 도면 일괄 업로드
- BOM PDF 파싱 및 계층 관리
- GT/참조도면 관리
"""

import json
import logging
import shutil
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query

from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetail,
    ProjectListResponse,
    ProjectBatchUploadRequest,
    ProjectBatchUploadResponse,
)
from schemas.quotation import QuotationExportRequest, QuotationExportFormat
from schemas.bom_item import (
    BOMHierarchyResponse,
    DrawingMatchRequest,
    DrawingMatchResult,
    SessionBatchCreateRequest,
    SessionBatchCreateResponse,
)
from services.project_service import get_project_service, ProjectService
from services.template_service import get_template_service, TemplateService
from services.bom_pdf_parser import BOMPDFParser
from services.drawing_matcher import DrawingMatcher

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


# =============================================================================
# BOM 계층 워크플로우 API
# =============================================================================

@router.post("/{project_id}/import-bom")
async def import_bom_pdf(
    project_id: str,
    file: UploadFile = File(...),
):
    """BOM PDF 업로드 → 파싱 → 계층 구조 생성

    BOM PDF의 테이블을 추출하고 행 배경색으로 계층을 분류합니다.
    - PINK: Assembly (조립체)
    - BLUE: Subassembly (하위 조립체)
    - WHITE: Part (단품, 견적 대상)

    Args:
        project_id: 프로젝트 ID
        file: BOM PDF 파일

    Returns:
        파싱된 BOM 계층 데이터
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # PDF 확장자 확인
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원합니다")

    # BOM PDF 저장
    project_dir = project_service.projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    bom_pdf_path = project_dir / "bom_source.pdf"
    content = await file.read()
    with open(bom_pdf_path, "wb") as f:
        f.write(content)

    # BOM PDF 파싱
    try:
        parser = BOMPDFParser()
        bom_data = parser.parse_bom_pdf(str(bom_pdf_path))
    except Exception as e:
        logger.error(f"BOM PDF 파싱 실패: {e}")
        raise HTTPException(status_code=500, detail=f"BOM PDF 파싱 실패: {str(e)}")

    # BOM 데이터 저장
    parser.save_bom_items(project_dir, bom_data)

    # 프로젝트 메타데이터 업데이트
    from schemas.project import ProjectUpdate
    project_service.update_project(project_id, ProjectUpdate(
        bom_source=file.filename,
    ))
    # 통계 직접 업데이트 (schema 외 필드)
    proj = project_service.get_project(project_id)
    proj["bom_item_count"] = bom_data["total_items"]
    proj["quotation_item_count"] = bom_data["part_count"]
    project_service._save_project(project_id)

    logger.info(f"BOM PDF import 완료: {project_id} → {bom_data['total_items']}개 항목")

    return {
        "project_id": project_id,
        "source_file": file.filename,
        "total_items": bom_data["total_items"],
        "assembly_count": bom_data["assembly_count"],
        "subassembly_count": bom_data["subassembly_count"],
        "part_count": bom_data["part_count"],
        "items": bom_data["items"],
    }


@router.get("/{project_id}/bom-hierarchy", response_model=BOMHierarchyResponse)
async def get_bom_hierarchy(project_id: str):
    """BOM 계층 트리 조회

    Args:
        project_id: 프로젝트 ID

    Returns:
        BOM 계층 트리 + 통계
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    parser = BOMPDFParser()
    bom_data = parser.load_bom_items(project_dir)

    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다. 먼저 import-bom을 실행하세요.")

    return BOMHierarchyResponse(
        project_id=project_id,
        bom_source=bom_data.get("source_file", ""),
        total_items=bom_data.get("total_items", 0),
        assembly_count=bom_data.get("assembly_count", 0),
        subassembly_count=bom_data.get("subassembly_count", 0),
        part_count=bom_data.get("part_count", 0),
        items=bom_data.get("items", []),
        hierarchy=bom_data.get("hierarchy", []),
    )


@router.post("/{project_id}/match-drawings", response_model=DrawingMatchResult)
async def match_drawings(
    project_id: str,
    request: DrawingMatchRequest,
):
    """도면번호 → PJT 폴더 매칭

    BOM 항목의 도면번호를 지정된 폴더에서 검색하여 매칭합니다.

    Args:
        project_id: 프로젝트 ID
        request: 도면 폴더 경로

    Returns:
        매칭 결과 (매칭 성공/실패 항목별)
    """
    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    parser = BOMPDFParser()
    bom_data = parser.load_bom_items(project_dir)

    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다. 먼저 import-bom을 실행하세요.")

    # 도면 매칭
    folder_path = Path(request.drawing_folder)
    if not folder_path.exists():
        raise HTTPException(status_code=400, detail=f"도면 폴더를 찾을 수 없습니다: {request.drawing_folder}")

    matcher = DrawingMatcher()
    items = bom_data["items"]
    matched_items = matcher.match_drawings(items, request.drawing_folder)

    # BOM 데이터 업데이트 (매칭 결과 저장)
    bom_data["items"] = matched_items
    parser.save_bom_items(project_dir, bom_data)

    # 프로젝트에 drawing_folder 저장
    project_service.update_project(project_id, ProjectUpdate(
        drawing_folder=request.drawing_folder,
    ))

    summary = matcher.get_match_summary(matched_items)

    return DrawingMatchResult(
        project_id=project_id,
        total_items=summary["total_items"],
        matched_count=summary["matched_count"],
        unmatched_count=summary["unmatched_count"],
        items=matched_items,
    )


@router.post("/{project_id}/create-sessions", response_model=SessionBatchCreateResponse)
async def create_sessions_from_bom(
    project_id: str,
    request: SessionBatchCreateRequest = None,
):
    """매칭된 도면 → 세션 일괄 생성

    WHITE(part) 항목 중 매칭된 도면이 있는 항목에 대해 세션을 생성합니다.
    각 세션에는 BOM 메타데이터(drawing_number, material, quantity 등)가 태깅됩니다.

    Args:
        project_id: 프로젝트 ID
        request: 세션 생성 옵션

    Returns:
        생성된 세션 목록
    """
    from routers.session_router import get_session_service
    import uuid

    if request is None:
        request = SessionBatchCreateRequest()

    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    # BOM 데이터 로드
    project_dir = project_service.projects_dir / project_id
    bom_parser = BOMPDFParser()
    bom_data = bom_parser.load_bom_items(project_dir)

    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다. 먼저 import-bom을 실행하세요.")

    # 세션 서비스 가져오기
    try:
        session_service = get_session_service()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="세션 서비스가 초기화되지 않았습니다"
        )

    # WHITE(part) 항목만 필터
    part_items = [
        item for item in bom_data["items"]
        if item.get("needs_quotation", False)
    ]

    created_sessions = []
    skipped = 0
    failed = 0

    for item in part_items:
        matched_file = item.get("matched_file")

        # 매칭된 파일이 없으면 건너뛰기
        if request.only_matched and not matched_file:
            skipped += 1
            continue

        # 이미 세션이 생성된 항목은 건너뛰기
        if item.get("session_id"):
            skipped += 1
            continue

        try:
            session_id = str(uuid.uuid4())

            # 매칭된 도면 파일을 세션 디렉토리에 복사
            upload_dir = Path("/app/data")
            session_dir = upload_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            file_path = ""
            image_width, image_height = None, None

            if matched_file and Path(matched_file).exists():
                src_path = Path(matched_file)
                dest_path = session_dir / f"original{src_path.suffix}"
                shutil.copy2(str(src_path), str(dest_path))
                file_path = str(dest_path)

                # 이미지인 경우 크기 추출
                if src_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".tif"}:
                    try:
                        from PIL import Image
                        with Image.open(dest_path) as img:
                            image_width, image_height = img.size
                    except Exception:
                        pass

            # BOM 메타데이터 구성
            metadata = {
                "drawing_number": item.get("drawing_number", ""),
                "bom_item_no": item.get("item_no", ""),
                "bom_level": item.get("level", "part"),
                "material": item.get("material", ""),
                "bom_quantity": item.get("quantity", 1),
                "bom_description": item.get("description", ""),
                "quote_status": "pending",
            }

            # 세션 생성
            session = session_service.create_session(
                session_id=session_id,
                filename=Path(matched_file).name if matched_file else f"{item.get('drawing_number', 'unknown')}.pdf",
                file_path=file_path,
                drawing_type="dimension_bom",
                image_width=image_width,
                image_height=image_height,
                features=["dimension_ocr", "table_extraction"],
                project_id=project_id,
                metadata=metadata,
            )

            # BOM 항목에 세션 ID 기록
            item["session_id"] = session_id

            created_sessions.append({
                "session_id": session_id,
                "drawing_number": item.get("drawing_number"),
                "description": item.get("description"),
                "material": item.get("material"),
                "filename": session.get("filename"),
            })

        except Exception as e:
            logger.error(f"세션 생성 실패 ({item.get('drawing_number')}): {e}")
            failed += 1

    # BOM 데이터 업데이트 (세션 ID 저장)
    bom_parser.save_bom_items(project_dir, bom_data)

    # 프로젝트 통계 업데이트
    proj = project_service.get_project(project_id)
    proj["session_count"] = proj.get("session_count", 0) + len(created_sessions)
    project_service._save_project(project_id)

    message = f"{len(created_sessions)}개 세션 생성 완료"
    if skipped > 0:
        message += f", {skipped}개 건너뜀"
    if failed > 0:
        message += f", {failed}개 실패"

    logger.info(f"세션 일괄 생성: {project_id} → {message}")

    return SessionBatchCreateResponse(
        project_id=project_id,
        created_count=len(created_sessions),
        skipped_count=skipped,
        failed_count=failed,
        sessions=created_sessions,
        message=message,
    )


# =============================================================================
# 견적 집계 API (Phase 3)
# =============================================================================

@router.get("/{project_id}/quotation")
async def get_project_quotation(
    project_id: str,
    refresh: bool = Query(False, description="강제 재계산 여부"),
):
    """프로젝트 견적 집계 조회

    - refresh=False: 캐시된 quotation.json 반환 (있으면)
    - refresh=True: 강제 재계산

    Args:
        project_id: 프로젝트 ID
        refresh: 강제 재계산 여부

    Returns:
        ProjectQuotationResponse: 견적 집계 데이터
    """
    from routers.session_router import get_session_service
    from services.quotation_service import get_quotation_service

    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    quotation_service = get_quotation_service()

    # 캐시 확인
    if not refresh:
        cached = quotation_service._load_quotation(project_id, project_service)
        if cached:
            return cached

    # 재계산
    try:
        session_service = get_session_service()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="세션 서비스가 초기화되지 않았습니다"
        )

    result = quotation_service.aggregate_quotation(
        project_id, project_service, session_service
    )

    logger.info(f"견적 집계 완료: {project_id} → {result.summary.total_sessions}개 세션")

    return result


@router.post("/{project_id}/quotation/export")
async def export_project_quotation(
    project_id: str,
    request: QuotationExportRequest = None,
):
    """견적서 내보내기 (PDF/Excel)

    Args:
        project_id: 프로젝트 ID
        request: 내보내기 옵션

    Returns:
        QuotationExportResponse: 내보내기 결과
    """
    from routers.session_router import get_session_service
    from services.quotation_service import get_quotation_service

    if request is None:
        request = QuotationExportRequest()

    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    quotation_service = get_quotation_service()

    # 먼저 집계 데이터 확보 (캐시 또는 재계산)
    quotation_data = quotation_service._load_quotation(project_id, project_service)
    if not quotation_data:
        try:
            session_service = get_session_service()
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="세션 서비스가 초기화되지 않았습니다"
            )
        quotation_data = quotation_service.aggregate_quotation(
            project_id, project_service, session_service
        )

    # 내보내기
    try:
        result = quotation_service.export(
            quotation_data=quotation_data,
            format=request.format,
            customer_name=request.customer_name,
            include_material_breakdown=request.include_material_breakdown,
            notes=request.notes,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"견적서 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail=f"견적서 내보내기 실패: {str(e)}")

    logger.info(f"견적서 내보내기 완료: {project_id} → {result.filename}")

    return result


@router.get("/{project_id}/quotation/download")
async def download_project_quotation(
    project_id: str,
    format: str = Query("pdf", description="다운로드 형식 (pdf/excel)"),
):
    """견적서 파일 다운로드

    Args:
        project_id: 프로젝트 ID
        format: 다운로드 형식

    Returns:
        FileResponse: 견적서 파일
    """
    from fastapi.responses import FileResponse
    from services.quotation_service import get_quotation_service

    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    quotation_service = get_quotation_service()

    # 파일 경로 결정
    if format == "excel":
        file_path = quotation_service.output_dir / f"quotation_{project_id}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"quotation_{project_id}.xlsx"
    else:
        file_path = quotation_service.output_dir / f"quotation_{project_id}.pdf"
        media_type = "application/pdf"
        filename = f"quotation_{project_id}.pdf"

    if not file_path.exists():
        # 파일이 없으면 먼저 생성
        from routers.session_router import get_session_service

        quotation_data = quotation_service._load_quotation(project_id, project_service)
        if not quotation_data:
            try:
                session_service = get_session_service()
            except Exception:
                raise HTTPException(
                    status_code=500,
                    detail="세션 서비스가 초기화되지 않았습니다"
                )
            quotation_data = quotation_service.aggregate_quotation(
                project_id, project_service, session_service
            )

        export_format = (
            QuotationExportFormat.EXCEL if format == "excel"
            else QuotationExportFormat.PDF
        )
        try:
            quotation_service.export(
                quotation_data=quotation_data,
                format=export_format,
            )
        except NotImplementedError as e:
            raise HTTPException(status_code=501, detail=str(e))

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="견적서 파일을 생성할 수 없습니다")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


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
