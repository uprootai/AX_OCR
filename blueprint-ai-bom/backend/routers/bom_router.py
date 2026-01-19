"""BOM Router - BOM 생성 및 내보내기 API 엔드포인트"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from schemas.bom import BOMData, BOMExportRequest, BOMExportResponse, ExportFormat


router = APIRouter(prefix="/bom", tags=["bom"])


# 테이블 추출 응답 모델
class ExtractedBOMItemResponse(BaseModel):
    """추출된 BOM 항목 응답"""
    item_no: Optional[int] = None
    part_name: str = ""
    material: str = ""
    quantity: int = 1
    spec: str = ""
    remark: str = ""


class BOMTableExtractionResponse(BaseModel):
    """BOM 테이블 추출 응답"""
    success: bool
    items: List[ExtractedBOMItemResponse] = []
    table_type: str = "unknown"
    rows: int = 0
    columns: int = 0
    raw_ocr_count: int = 0
    processing_time_ms: float = 0.0
    error_message: str = ""


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


@router.post("/extract-table", response_model=BOMTableExtractionResponse)
async def extract_bom_from_table(
    file: UploadFile = File(...),
    table_index: int = Query(default=0, description="추출할 테이블 인덱스"),
    conf_threshold: float = Query(default=0.1, description="테이블 검출 신뢰도 임계값")
):
    """
    도면 이미지에서 BOM 테이블 직접 추출

    TableTransformer + EasyOCR을 사용하여 도면의 테이블에서
    부품 정보(품번, 품명, 재질, 수량, 규격, 비고)를 추출합니다.

    - **file**: 도면 이미지 파일 (jpg, png)
    - **table_index**: 여러 테이블이 있을 경우 추출할 테이블 인덱스 (기본: 0)
    - **conf_threshold**: 테이블 영역 검출 신뢰도 임계값 (기본: 0.1)
    """
    from services.bom_table_extractor import get_bom_table_extractor

    # 파일 확장자 확인
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식: {file_ext}. 지원 형식: {allowed_extensions}"
        )

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # BOM 테이블 추출
            extractor = get_bom_table_extractor()
            result = extractor.extract_from_image(
                tmp_path,
                conf_threshold=conf_threshold,
                table_index=table_index
            )

            # 응답 변환
            items = [
                ExtractedBOMItemResponse(
                    item_no=item.item_no,
                    part_name=item.part_name,
                    material=item.material,
                    quantity=item.quantity,
                    spec=item.spec,
                    remark=item.remark
                )
                for item in result.items
            ]

            return BOMTableExtractionResponse(
                success=result.success,
                items=items,
                table_type=result.table_type,
                rows=result.raw_structure.get("rows", 0) if result.raw_structure else 0,
                columns=result.raw_structure.get("columns", 0) if result.raw_structure else 0,
                raw_ocr_count=len(result.raw_ocr),
                processing_time_ms=result.processing_time_ms,
                error_message=result.error_message
            )

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-all-tables")
async def extract_all_bom_tables(
    file: UploadFile = File(...),
    conf_threshold: float = Query(default=0.1, description="테이블 검출 신뢰도 임계값")
):
    """
    도면 이미지에서 모든 BOM 테이블 추출

    이미지에서 검출된 모든 테이블 영역에서 BOM 데이터를 추출합니다.

    - **file**: 도면 이미지 파일
    - **conf_threshold**: 테이블 영역 검출 신뢰도 임계값
    """
    from services.bom_table_extractor import get_bom_table_extractor

    # 파일 확장자 확인
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식: {file_ext}"
        )

    try:
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 모든 테이블 추출
            extractor = get_bom_table_extractor()
            results = extractor.extract_all_tables(tmp_path, conf_threshold=conf_threshold)

            # 응답 변환
            tables = []
            for idx, result in enumerate(results):
                items = [
                    {
                        "item_no": item.item_no,
                        "part_name": item.part_name,
                        "material": item.material,
                        "quantity": item.quantity,
                        "spec": item.spec,
                        "remark": item.remark
                    }
                    for item in result.items
                ]

                tables.append({
                    "table_index": idx,
                    "success": result.success,
                    "table_type": result.table_type,
                    "items": items,
                    "rows": result.raw_structure.get("rows", 0) if result.raw_structure else 0,
                    "columns": result.raw_structure.get("columns", 0) if result.raw_structure else 0,
                    "bbox": result.table_bbox,
                    "processing_time_ms": result.processing_time_ms,
                    "error_message": result.error_message
                })

            return {
                "total_tables": len(tables),
                "tables": tables
            }

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
