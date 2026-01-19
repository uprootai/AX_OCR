"""
DWG Parsing Router
/api/v1/dwg 엔드포인트
"""

import time
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, File, UploadFile, Body, HTTPException
from pydantic import BaseModel

from services.dwg_service import (
    parse_dwg_bytes,
    parse_dxf,
    extract_pid_elements,
    get_dwg_info,
    is_oda_available,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dwg", tags=["DWG"])


# =====================
# Schemas
# =====================

class DWGParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


class DWGInfoResponse(BaseModel):
    oda_available: bool
    oda_path: Optional[str]
    supported_formats: list
    output_entities: list
    install_oda: str


# =====================
# Endpoints
# =====================

@router.get("/info", response_model=DWGInfoResponse)
async def dwg_info():
    """
    DWG 파싱 기능 정보

    - ODA File Converter 설치 여부
    - 지원 포맷
    - 추출 가능한 엔티티 타입
    """
    info = get_dwg_info()
    return DWGInfoResponse(**info)


@router.post("/parse", response_model=DWGParseResponse)
async def parse_dwg_file(
    file: UploadFile = File(..., description="DWG 또는 DXF 파일"),
    extract_pid: bool = Body(default=True, embed=True, description="P&ID 요소 추출 여부")
):
    """
    DWG/DXF 파일 파싱

    **지원 포맷:**
    - DWG: ODA File Converter 필요 (없으면 오류)
    - DXF: ezdxf로 직접 파싱

    **추출 데이터:**
    - metadata: 버전, 단위, 도면 범위
    - layers: 레이어 목록
    - entities: LINE, POLYLINE, CIRCLE, ARC, TEXT, MTEXT, INSERT
    - blocks: 블록 정의

    **P&ID 추출 (extract_pid=true):**
    - lines: 배관/신호선
    - symbols: 블록 참조 (심볼 후보)
    - texts: 텍스트 (태그/라벨)
    """
    start_time = time.time()

    # 파일 확장자 확인
    filename = file.filename or "drawing.dwg"
    if not filename.lower().endswith((".dwg", ".dxf")):
        return DWGParseResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error="Unsupported file format. Use .dwg or .dxf"
        )

    # DWG인데 ODA 없으면 경고
    if filename.lower().endswith(".dwg") and not is_oda_available():
        return DWGParseResponse(
            success=False,
            data={
                "oda_available": False,
                "suggestion": "Install ODA File Converter or convert to DXF first"
            },
            processing_time=time.time() - start_time,
            error="ODA File Converter not installed. DWG files require ODA for conversion."
        )

    try:
        # 파일 읽기
        file_bytes = await file.read()

        # 파싱
        parsed_data = parse_dwg_bytes(file_bytes, filename)

        if "error" in parsed_data:
            return DWGParseResponse(
                success=False,
                data=parsed_data,
                processing_time=time.time() - start_time,
                error=parsed_data["error"]
            )

        # P&ID 요소 추출
        if extract_pid:
            pid_elements = extract_pid_elements(parsed_data)
            parsed_data["pid_elements"] = pid_elements

        return DWGParseResponse(
            success=True,
            data=parsed_data,
            processing_time=round(time.time() - start_time, 3)
        )

    except Exception as e:
        logger.error(f"DWG parse error: {e}")
        import traceback
        traceback.print_exc()
        return DWGParseResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/parse-dxf", response_model=DWGParseResponse)
async def parse_dxf_file(
    file: UploadFile = File(..., description="DXF 파일"),
    extract_pid: bool = Body(default=True, embed=True, description="P&ID 요소 추출 여부")
):
    """
    DXF 파일 직접 파싱 (ODA 불필요)

    DXF 파일을 업로드하여 엔티티를 추출합니다.
    """
    start_time = time.time()

    filename = file.filename or "drawing.dxf"
    if not filename.lower().endswith(".dxf"):
        return DWGParseResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error="This endpoint only accepts .dxf files"
        )

    try:
        file_bytes = await file.read()
        parsed_data = parse_dwg_bytes(file_bytes, filename)

        if "error" in parsed_data:
            return DWGParseResponse(
                success=False,
                data=parsed_data,
                processing_time=time.time() - start_time,
                error=parsed_data["error"]
            )

        if extract_pid:
            pid_elements = extract_pid_elements(parsed_data)
            parsed_data["pid_elements"] = pid_elements

        return DWGParseResponse(
            success=True,
            data=parsed_data,
            processing_time=round(time.time() - start_time, 3)
        )

    except Exception as e:
        logger.error(f"DXF parse error: {e}")
        return DWGParseResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/extract-pid", response_model=DWGParseResponse)
async def extract_pid_from_file(
    file: UploadFile = File(..., description="DWG 또는 DXF 파일")
):
    """
    P&ID 요소만 추출 (간소화된 응답)

    **응답:**
    - lines: 연결선 좌표
    - symbols: 블록 참조 (심볼 후보)
    - texts: 텍스트 (태그/라벨)

    **용도:**
    - Line Detector 대체
    - OCR 대체 (CAD 텍스트)
    - 심볼 위치 추출
    """
    start_time = time.time()

    filename = file.filename or "drawing.dwg"

    # DWG인데 ODA 없으면 경고
    if filename.lower().endswith(".dwg") and not is_oda_available():
        return DWGParseResponse(
            success=False,
            data={"oda_available": False},
            processing_time=time.time() - start_time,
            error="ODA File Converter required for DWG files"
        )

    try:
        file_bytes = await file.read()
        parsed_data = parse_dwg_bytes(file_bytes, filename)

        if "error" in parsed_data:
            return DWGParseResponse(
                success=False,
                data=parsed_data,
                processing_time=time.time() - start_time,
                error=parsed_data["error"]
            )

        # P&ID 요소만 추출
        pid_elements = extract_pid_elements(parsed_data)

        return DWGParseResponse(
            success=True,
            data=pid_elements,
            processing_time=round(time.time() - start_time, 3)
        )

    except Exception as e:
        logger.error(f"P&ID extraction error: {e}")
        return DWGParseResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.get("/layers")
async def get_supported_layers():
    """
    P&ID 도면에서 일반적으로 사용되는 레이어 목록

    TECHCROSS BWMS 도면 레이어 참조
    """
    return {
        "common_layers": [
            {"name": "0", "description": "기본 레이어"},
            {"name": "PIPE", "description": "배관"},
            {"name": "PROCESS", "description": "프로세스 라인"},
            {"name": "SIGNAL", "description": "신호선"},
            {"name": "INSTRUMENT", "description": "계기"},
            {"name": "VALVE", "description": "밸브"},
            {"name": "EQUIPMENT", "description": "장비"},
            {"name": "TEXT", "description": "텍스트/라벨"},
            {"name": "DIMENSION", "description": "치수"},
            {"name": "BORDER", "description": "도면 테두리"},
        ],
        "bwms_specific": [
            {"name": "BWMS_SIGNAL", "description": "BWMS 신호선"},
            {"name": "BWMS_VALVE", "description": "BWMS 밸브"},
            {"name": "SEA_CHEST", "description": "Sea Chest 관련"},
            {"name": "BALLAST", "description": "밸러스트 라인"},
        ]
    }
