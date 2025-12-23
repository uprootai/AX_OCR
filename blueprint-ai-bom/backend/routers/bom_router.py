"""BOM Router - BOM 생성 및 내보내기 API 엔드포인트"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from schemas.bom import BOMData, BOMExportRequest, BOMExportResponse, ExportFormat


router = APIRouter(prefix="/bom", tags=["bom"])


# 의존성 주입을 위한 전역 서비스
_bom_service = None
_session_service = None


def set_bom_service(bom_service, session_service):
    """서비스 인스턴스 설정"""
    global _bom_service, _session_service
    _bom_service = bom_service
    _session_service = session_service


def get_bom_service():
    """BOM 서비스 의존성"""
    if _bom_service is None:
        raise HTTPException(status_code=500, detail="BOM service not initialized")
    return _bom_service


def get_session_service():
    """세션 서비스 의존성"""
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


@router.post("/{session_id}/generate")
async def generate_bom(session_id: str):
    """BOM 생성"""
    bom_service = get_bom_service()
    session_service = get_session_service()

    # 세션 확인
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    detections = session.get("detections", [])
    if not detections:
        raise HTTPException(status_code=400, detail="검출 결과가 없습니다")

    # 승인된 검출 확인
    approved = [
        d for d in detections
        if d.get("verification_status") in ("approved", "modified", "manual")
    ]
    if not approved:
        raise HTTPException(status_code=400, detail="승인된 검출이 없습니다")

    # 상태 업데이트
    from schemas.session import SessionStatus
    session_service.update_status(session_id, SessionStatus.GENERATING_BOM)

    try:
        # BOM 생성
        bom_data = bom_service.generate_bom(
            session_id=session_id,
            detections=detections,
            dimensions=session.get("dimensions"),
            links=session.get("dimension_symbol_links"),
            filename=session.get("filename"),
            model_id=session.get("model_id")
        )

        # 세션에 BOM 저장
        session_service.set_bom_data(session_id, bom_data)

        return bom_data

    except Exception as e:
        session_service.update_status(
            session_id,
            SessionStatus.ERROR,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_bom(session_id: str):
    """BOM 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    bom_data = session.get("bom_data")
    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM이 생성되지 않았습니다")

    return bom_data


@router.post("/{session_id}/export")
async def export_bom(session_id: str, request: BOMExportRequest):
    """BOM 내보내기"""
    bom_service = get_bom_service()
    session_service = get_session_service()

    # 세션 확인
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    bom_data = session.get("bom_data")
    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM이 생성되지 않았습니다")

    try:
        # 내보내기 실행
        output_path = bom_service.export(
            bom_data=bom_data,
            format=request.format,
            customer_name=request.customer_name
        )

        from datetime import datetime

        return BOMExportResponse(
            session_id=session_id,
            format=request.format,
            filename=output_path.name,
            file_path=str(output_path),
            file_size=output_path.stat().st_size,
            created_at=datetime.now()
        )

    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/download")
async def download_bom(
    session_id: str,
    format: ExportFormat = Query(default=ExportFormat.EXCEL)
):
    """BOM 파일 다운로드"""
    bom_service = get_bom_service()
    session_service = get_session_service()

    # 세션 확인
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    bom_data = session.get("bom_data")
    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM이 생성되지 않았습니다")

    try:
        # 내보내기 실행
        output_path = bom_service.export(
            bom_data=bom_data,
            format=format
        )

        # MIME 타입 결정
        mime_types = {
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json",
            ExportFormat.PDF: "application/pdf",
        }

        return FileResponse(
            path=str(output_path),
            media_type=mime_types.get(format, "application/octet-stream"),
            filename=output_path.name
        )

    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/summary")
async def get_bom_summary(session_id: str):
    """BOM 요약 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    bom_data = session.get("bom_data")
    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM이 생성되지 않았습니다")

    return {
        "session_id": session_id,
        "summary": bom_data.get("summary"),
        "item_count": len(bom_data.get("items", [])),
        "detection_count": bom_data.get("detection_count"),
        "approved_count": bom_data.get("approved_count"),
        "created_at": bom_data.get("created_at"),
    }
