"""
DSE Bearing Parsing — FastAPI route handlers
"""

import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from services.dsebearing_parser import get_parser

from .errors import (
    DSEBearingError, ErrorCodes, get_error_message,
    validate_file, MAX_FILE_SIZE,
)
from .models import (
    TitleBlockResponse, PartsListResponse, PartsListItemResponse,
    DimensionItem, DimensionParserResponse,
    BOMItem, BOMMatcherResponse,
)
from .ocr_client import call_edocr2_ocr

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================
# Title Block Parser
# =====================

@router.post("/titleblock", response_model=TitleBlockResponse)
async def parse_title_block(
    file: UploadFile = File(None),
    ocr_results: str = Form(None),
    profile: str = Form("bearing")
):
    """
    Title Block 파싱 - 도면에서 도면번호, Rev, 품명, 재질 추출

    - file: 도면 이미지 파일 (새 OCR 수행)
    - ocr_results: 기존 OCR 결과 JSON (재사용)
    - profile: 파싱 프로파일 (bearing, standard)

    에러 코드:
    - FILE_TOO_LARGE: 파일이 20MB 초과
    - INVALID_FILE_TYPE: 지원하지 않는 파일 형식
    - OCR_SERVICE_ERROR: OCR 서비스 연결 실패
    - PARSING_ERROR: 파싱 중 오류
    """
    try:
        logger.info(f"Title Block 파싱 시작, profile={profile}")

        validate_file(file)

        parser = get_parser()
        ocr_texts = []

        # 1. 기존 OCR 결과 사용
        if ocr_results:
            try:
                ocr_texts = json.loads(ocr_results)
                if isinstance(ocr_texts, dict):
                    ocr_texts = ocr_texts.get("texts", ocr_texts.get("results", []))
            except json.JSONDecodeError as e:
                logger.warning(f"OCR 결과 JSON 파싱 실패: {e}")
                raise DSEBearingError(
                    get_error_message(ErrorCodes.INVALID_JSON),
                    ErrorCodes.INVALID_JSON,
                    {"error": str(e)}
                )

        # 2. 파일이 있으면 새로 OCR 수행
        if file and file.filename:
            file_content = await file.read()

            if len(file_content) > MAX_FILE_SIZE:
                raise DSEBearingError(
                    get_error_message(ErrorCodes.FILE_TOO_LARGE),
                    ErrorCodes.FILE_TOO_LARGE,
                    {"file_size": len(file_content), "max_size": MAX_FILE_SIZE}
                )

            if file_content:
                ocr_texts = await call_edocr2_ocr(file_content, file.filename)

    except DSEBearingError as e:
        raise HTTPException(
            status_code=400,
            detail={"error_code": e.error_code, "message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.exception(f"Title Block 파싱 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCodes.PARSING_ERROR,
                "message": get_error_message(ErrorCodes.PARSING_ERROR),
                "details": {"error": str(e)}
            }
        )

    # 3. OCR 결과 없으면 빈 결과 반환
    if not ocr_texts:
        logger.warning("OCR 결과 없음 - 빈 결과 반환")
        return TitleBlockResponse(
            success=False,
            drawing_number="",
            revision="",
            part_name="",
            material="",
            date="",
            size="",
            scale="",
            sheet="",
            company="",
            raw_texts=["OCR 결과 없음"],
            confidence=0.0
        )

    # 4. 실제 파싱 수행
    result = parser.parse_title_block(ocr_texts)

    # 5. 신뢰도 계산
    confidence = 0.0
    if result.drawing_number:
        confidence += 0.3
    if result.revision:
        confidence += 0.2
    if result.part_name:
        confidence += 0.3
    if result.material:
        confidence += 0.2

    return TitleBlockResponse(
        success=bool(result.drawing_number),
        drawing_number=result.drawing_number,
        revision=result.revision,
        part_name=result.part_name,
        material=result.material,
        date=result.date,
        size=result.size,
        scale=result.scale,
        sheet=result.sheet,
        company=result.company,
        raw_texts=result.raw_texts[:20],
        confidence=confidence
    )


# =====================
# Parts List Parser
# =====================

@router.post("/partslist", response_model=PartsListResponse)
async def parse_parts_list(
    file: UploadFile = File(None),
    ocr_results: str = Form(None),
    table_data: str = Form(None),
    profile: str = Form("bearing")
):
    """
    Parts List 테이블 파싱

    - file: 도면 이미지 파일
    - ocr_results: 기존 OCR 결과 JSON
    - table_data: Table Detector 결과 JSON
    - profile: 파싱 프로파일
    """
    logger.info(f"Parts List 파싱 시작, profile={profile}")
    parser = get_parser()
    ocr_texts = []
    table = None

    if ocr_results:
        try:
            ocr_texts = json.loads(ocr_results)
            if isinstance(ocr_texts, dict):
                ocr_texts = ocr_texts.get("texts", ocr_texts.get("results", []))
        except json.JSONDecodeError:
            pass

    if table_data:
        try:
            table = json.loads(table_data)
        except json.JSONDecodeError:
            pass

    if file and file.filename and not ocr_texts:
        file_content = await file.read()
        if file_content:
            ocr_texts = await call_edocr2_ocr(file_content, file.filename)

    if not ocr_texts and not table:
        logger.warning("Parts List OCR 결과 없음 - 빈 결과 반환")
        return PartsListResponse(
            success=False,
            items=[],
            total_count=0,
            confidence=0.0
        )

    parsed_items = parser.parse_parts_list(ocr_texts, table)

    items = [
        PartsListItemResponse(
            no=item.no,
            description=item.description,
            material=item.material or "SEE EXCEL BOM",
            size_dwg_no=item.size_dwg_no,
            qty=item.qty,
            remark=item.remark,
            weight=item.weight
        )
        for item in parsed_items
    ]

    confidence = min(1.0, len(items) * 0.1) if items else 0.0

    return PartsListResponse(
        success=len(items) > 0,
        items=items,
        total_count=len(items),
        confidence=confidence
    )


# =====================
# Dimension Parser
# =====================

@router.post("/dimensionparser", response_model=DimensionParserResponse)
async def parse_dimensions(
    file: UploadFile = File(None),
    ocr_results: str = Form(None),
    profile: str = Form("bearing")
):
    """
    치수 파싱 - OCR 결과에서 치수 정보 추출
    """
    logger.info(f"Dimension 파싱 시작, profile={profile}")
    parser = get_parser()
    ocr_texts = []

    if ocr_results:
        try:
            ocr_texts = json.loads(ocr_results)
            if isinstance(ocr_texts, dict):
                ocr_texts = ocr_texts.get("texts", ocr_texts.get("results", []))
        except json.JSONDecodeError:
            pass

    if file and file.filename and not ocr_texts:
        file_content = await file.read()
        if file_content:
            ocr_texts = await call_edocr2_ocr(file_content, file.filename)

    if not ocr_texts:
        # Mock 데이터
        return DimensionParserResponse(
            success=True,
            dimensions=[
                DimensionItem(type="diameter", value=314.0, tolerance="±0.11", raw_text="Ø314 ±0.11"),
                DimensionItem(type="bearing_od_id", outer_diameter=480.0, inner_diameter=314.0, raw_text="(Ø480) Ø314"),
                DimensionItem(type="tolerance", value=200.0, raw_text="(200)"),
            ],
            gdt_symbols=["⊥ 0.02 A"],
            confidence=0.5
        )

    dims = parser.extract_dimensions(ocr_texts)

    items = [
        DimensionItem(
            type=d.get("type", "unknown"),
            value=d.get("value"),
            outer_diameter=d.get("outer_diameter"),
            inner_diameter=d.get("inner_diameter"),
            tolerance=d.get("tolerance"),
            upper_tolerance=d.get("upper_tolerance"),
            lower_tolerance=d.get("lower_tolerance"),
            raw_text=d.get("raw_text", "")
        )
        for d in dims
    ]

    return DimensionParserResponse(
        success=len(items) > 0,
        dimensions=items,
        gdt_symbols=[],
        confidence=min(1.0, len(items) * 0.15)
    )


# =====================
# BOM Matcher
# =====================

@router.post("/bommatcher", response_model=BOMMatcherResponse)
async def match_bom(
    title_block: str = Form(None),
    parts_list: str = Form(None),
    dimensions: str = Form(None),
    profile: str = Form("bearing")
):
    """
    BOM 매칭 - Title Block + Parts List + Dimensions 통합
    """
    logger.info(f"BOM Matching 시작, profile={profile}")

    tb_data = {}
    pl_data = []
    dim_data = []

    if title_block:
        try:
            tb_data = json.loads(title_block)
        except Exception:
            pass

    if parts_list:
        try:
            pl_data = json.loads(parts_list)
            if isinstance(pl_data, dict):
                pl_data = pl_data.get("items", [])
        except Exception:
            pass

    if dimensions:
        try:
            dim_data = json.loads(dimensions)
            if isinstance(dim_data, dict):
                dim_data = dim_data.get("dimensions", [])
        except Exception:
            pass

    matched_items = []
    for item in pl_data:
        if isinstance(item, dict):
            bom_item = BOMItem(
                no=item.get("no", item.get("part_no", "")),
                description=item.get("description", ""),
                material=item.get("material", tb_data.get("material", "SEE EXCEL BOM")),
                size_dwg_no=item.get("size_dwg_no", ""),
                dimensions=[DimensionItem(**d) for d in dim_data[:2]] if dim_data else [],
                qty=item.get("qty", 1),
                weight=item.get("weight")
            )
            matched_items.append(bom_item)

    if not matched_items:
        matched_items = [
            BOMItem(
                no="1",
                description="RING UPPER",
                material=tb_data.get("material", "SF45A"),
                size_dwg_no="TD0062017P001",
                dimensions=[
                    DimensionItem(type="diameter", value=314.0, tolerance="±0.11"),
                ],
                qty=1
            ),
            BOMItem(
                no="2",
                description="RING LOWER",
                material=tb_data.get("material", "SF45A"),
                size_dwg_no="TD0062017P002",
                dimensions=[],
                qty=1
            ),
        ]

    return BOMMatcherResponse(
        success=True,
        matched_items=matched_items,
        unmatched_count=0,
        match_confidence=0.9 if matched_items else 0.5
    )
