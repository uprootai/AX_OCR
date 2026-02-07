"""Quotation Router - 견적 집계 API (Phase 3)

프로젝트 견적 조회, 내보내기, 다운로드, 어셈블리 단위 견적서
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from schemas.quotation import QuotationExportRequest, QuotationExportFormat
from services.project_service import get_project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["quotation"])


def get_services():
    """서비스 의존성"""
    data_dir = Path("/app/data")
    return {
        "project_service": get_project_service(data_dir),
    }


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


@router.get("/{project_id}/quotation/assembly/{assembly_dwg}/download")
async def download_assembly_quotation(
    project_id: str,
    assembly_dwg: str,
    format: str = Query("pdf", description="다운로드 형식 (pdf/excel)"),
):
    """어셈블리 단위 견적서 파일 다운로드

    Args:
        project_id: 프로젝트 ID
        assembly_dwg: 어셈블리 도면번호
        format: 다운로드 형식 (pdf/excel)

    Returns:
        FileResponse: 견적서 파일
    """
    from fastapi.responses import FileResponse
    from services.quotation_service import get_quotation_service
    from routers.session_router import get_session_service

    services = get_services()
    project_service = services["project_service"]

    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

    quotation_service = get_quotation_service()

    # 견적 데이터 로드 또는 생성
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

    # 어셈블리 존재 확인
    assy_group = next(
        (g for g in quotation_data.assembly_groups
         if g.assembly_drawing_number == assembly_dwg),
        None
    )
    if not assy_group:
        raise HTTPException(status_code=404, detail=f"어셈블리를 찾을 수 없습니다: {assembly_dwg}")

    # 파일 경로 및 생성
    safe_assy = assembly_dwg.replace("/", "_").replace(" ", "_")
    export_format = (
        QuotationExportFormat.EXCEL if format == "excel"
        else QuotationExportFormat.PDF
    )

    try:
        result = quotation_service.export_assembly(
            quotation_data=quotation_data,
            assembly_drawing_number=assembly_dwg,
            format=export_format,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"어셈블리 견적서 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    file_path = Path(result.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="견적서 파일을 생성할 수 없습니다")

    if format == "excel":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"quotation_{project_id}_{safe_assy}.xlsx"
    else:
        media_type = "application/pdf"
        filename = f"quotation_{project_id}_{safe_assy}.pdf"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )
