"""
Region Text Extraction Router
/api/v1/region-rules/*, /api/v1/region-text/*, /api/v1/valve-signal/* 엔드포인트

영역 기반 텍스트 추출 및 밸브 시그널 리스트
"""

import os
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import APIRouter, File, UploadFile, Form, Body
from fastapi.responses import Response
from pydantic import BaseModel
import httpx

from region_extractor import (
    get_rule_manager,
    get_extractor,
    ExtractionRule,
    generate_valve_signal_excel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Region"])

# Configuration
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006/api/v1/ocr")
LINE_DETECTOR_API_URL = os.getenv("LINE_DETECTOR_API_URL", "http://line-detector-api:5016/api/v1/process")


# =====================
# Schemas
# =====================

class ProcessResponse(BaseModel):
    success: bool
    data: Dict
    processing_time: float
    error: Optional[str] = None


# =====================
# Region Rules Endpoints
# =====================

@router.get("/region-rules")
async def list_region_rules():
    """
    영역 추출 규칙 목록 조회

    UI에서 사용 가능한 모든 규칙 반환
    """
    rule_manager = get_rule_manager()
    rules = rule_manager.get_all_rules()

    return {
        "success": True,
        "data": {
            "rules": [rule.to_dict() for rule in rules],
            "total": len(rules),
            "enabled_count": len([r for r in rules if r.enabled])
        }
    }


@router.get("/region-rules/{rule_id}")
async def get_region_rule(rule_id: str):
    """
    특정 규칙 상세 조회
    """
    rule_manager = get_rule_manager()
    rule = rule_manager.get_rule(rule_id)

    if not rule:
        return {
            "success": False,
            "error": f"Rule '{rule_id}' not found"
        }

    return {
        "success": True,
        "data": rule.to_dict()
    }


@router.post("/region-rules")
async def create_region_rule(rule_data: Dict = Body(...)):
    """
    새 규칙 생성

    UI에서 새 규칙을 추가할 때 사용
    """
    try:
        rule = ExtractionRule.from_dict(rule_data)
        rule_manager = get_rule_manager()

        if rule_manager.add_rule(rule):
            return {
                "success": True,
                "data": rule.to_dict(),
                "message": f"Rule '{rule.id}' created successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Rule '{rule.id}' already exists"
            }

    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.put("/region-rules/{rule_id}")
async def update_region_rule(rule_id: str, rule_data: Dict = Body(...)):
    """
    규칙 업데이트

    UI에서 규칙을 편집할 때 사용
    """
    try:
        rule_manager = get_rule_manager()
        updated_rule = rule_manager.update_rule(rule_id, rule_data)

        if updated_rule:
            return {
                "success": True,
                "data": updated_rule.to_dict(),
                "message": f"Rule '{rule_id}' updated successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Rule '{rule_id}' not found"
            }

    except Exception as e:
        logger.error(f"Error updating rule: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/region-rules/{rule_id}")
async def delete_region_rule(rule_id: str):
    """
    규칙 삭제
    """
    rule_manager = get_rule_manager()

    if rule_manager.delete_rule(rule_id):
        return {
            "success": True,
            "message": f"Rule '{rule_id}' deleted successfully"
        }
    else:
        return {
            "success": False,
            "error": f"Rule '{rule_id}' not found"
        }


# =====================
# Region Text Extraction Endpoints
# =====================

@router.post("/region-text/extract", response_model=ProcessResponse)
async def extract_region_text(
    regions: List[Dict] = Body(..., description="Line Detector 영역 목록"),
    texts: List[Dict] = Body(..., description="PaddleOCR 텍스트 목록"),
    rule_ids: Optional[List[str]] = Body(default=None, description="적용할 규칙 ID 목록 (null=모든 활성 규칙)"),
    text_margin: float = Body(default=30, description="텍스트 매칭 마진 (픽셀)")
):
    """
    영역 기반 텍스트 추출 API

    Line Detector가 검출한 영역과 PaddleOCR이 검출한 텍스트를 매칭하여
    규칙에 따라 밸브 ID, 장비 태그 등을 추출합니다.

    Parameters:
    - regions: Line Detector의 detect_regions=true로 검출된 영역
    - texts: PaddleOCR 또는 다른 OCR 결과
    - rule_ids: 적용할 규칙 (null이면 활성화된 모든 규칙 적용)
    - text_margin: 영역 경계에서 텍스트 매칭 허용 마진

    Returns:
    - 규칙별 매칭 결과 및 추출된 항목
    """
    start_time = time.time()

    try:
        extractor = get_extractor()
        result = extractor.extract(
            regions=regions,
            texts=texts,
            rule_ids=rule_ids,
            text_margin=text_margin
        )

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data=result,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Region text extraction error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


# =====================
# Valve Signal Endpoints
# =====================

@router.post("/valve-signal/extract")
async def extract_valve_signal_list(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    rule_id: str = Form(default="valve_signal_bwms", description="적용할 규칙 ID"),
    language: str = Form(default="en", description="OCR 언어")
):
    """
    Valve Signal List 추출 API (이미지 입력)

    P&ID 이미지에서 Line Detector와 PaddleOCR을 호출하여
    SIGNAL FOR BWMS 등의 영역에서 밸브 ID를 추출합니다.

    내부적으로 다음 API를 호출합니다:
    1. Line Detector (detect_regions=true)
    2. PaddleOCR
    3. Region Text Extractor
    """
    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()

        async with httpx.AsyncClient(timeout=120.0) as client:
            # 1. Line Detector 호출
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {
                "detect_regions": "true",
                "classify_styles": "true",
                "min_region_area": "1000",
                "region_line_styles": "dashed,dash_dot"
            }
            line_response = await client.post(LINE_DETECTOR_API_URL, files=files, data=data)

            if line_response.status_code != 200:
                return ProcessResponse(
                    success=False,
                    data={},
                    processing_time=time.time() - start_time,
                    error=f"Line Detector API error: {line_response.status_code}"
                )

            line_result = line_response.json()
            regions = line_result.get("data", {}).get("regions", [])

            logger.info(f"Line Detector: {len(regions)} regions detected")

            # 2. PaddleOCR 호출
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {"language": language}
            ocr_response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

            if ocr_response.status_code != 200:
                return ProcessResponse(
                    success=False,
                    data={},
                    processing_time=time.time() - start_time,
                    error=f"PaddleOCR API error: {ocr_response.status_code}"
                )

            ocr_result = ocr_response.json()
            texts = ocr_result.get("detections", [])
            if not texts:
                texts = ocr_result.get("texts", [])

            logger.info(f"PaddleOCR: {len(texts)} texts detected")

        # 3. Region Text Extraction
        extractor = get_extractor()
        extraction_result = extractor.extract(
            regions=regions,
            texts=texts,
            rule_ids=[rule_id]
        )

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                **extraction_result,
                "line_detector": {
                    "total_lines": line_result.get("data", {}).get("total_lines", 0),
                    "total_regions": len(regions)
                },
                "ocr": {
                    "total_texts": len(texts)
                }
            },
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Valve signal extraction error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/valve-signal/export-excel")
async def export_valve_signal_excel(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    rule_id: str = Form(default="valve_signal_bwms", description="적용할 규칙 ID"),
    project_name: str = Form(default="Unknown Project", description="프로젝트명"),
    drawing_no: str = Form(default="N/A", description="도면 번호"),
    language: str = Form(default="en", description="OCR 언어")
):
    """
    Valve Signal List Excel 내보내기

    P&ID 이미지에서 밸브 시그널 리스트를 추출하고 Excel 파일로 내보냅니다.
    """
    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()

        async with httpx.AsyncClient(timeout=120.0) as client:
            # 1. Line Detector 호출
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {
                "detect_regions": "true",
                "classify_styles": "true",
                "min_region_area": "1000",
                "region_line_styles": "dashed,dash_dot"
            }
            line_response = await client.post(LINE_DETECTOR_API_URL, files=files, data=data)

            if line_response.status_code != 200:
                return ProcessResponse(
                    success=False,
                    data={},
                    processing_time=time.time() - start_time,
                    error=f"Line Detector API error: {line_response.status_code}"
                )

            line_result = line_response.json()
            regions = line_result.get("data", {}).get("regions", [])

            # 2. PaddleOCR 호출
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {"language": language}
            ocr_response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

            if ocr_response.status_code != 200:
                return ProcessResponse(
                    success=False,
                    data={},
                    processing_time=time.time() - start_time,
                    error=f"PaddleOCR API error: {ocr_response.status_code}"
                )

            ocr_result = ocr_response.json()
            texts = ocr_result.get("detections", [])
            if not texts:
                texts = ocr_result.get("texts", [])

        # 3. Region Text Extraction
        extractor = get_extractor()
        extraction_result = extractor.extract(
            regions=regions,
            texts=texts,
            rule_ids=[rule_id]
        )

        # 추출된 항목 가져오기
        all_items = extraction_result.get("all_extracted_items", [])

        if not all_items:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"No valve signals found with rule '{rule_id}'"
            )

        # 규칙 정보 가져오기
        rule_manager = get_rule_manager()
        rule = rule_manager.get_rule(rule_id)
        rule_name = rule.name if rule else "Valve Signal List"

        # Excel 생성
        project_info = {
            "name": project_name,
            "drawing_no": drawing_no,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        excel_bytes = generate_valve_signal_excel(
            extracted_items=all_items,
            project_info=project_info,
            rule_name=rule_name
        )

        # 파일명 생성
        filename = f"Valve_Signal_List_{drawing_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Generated Excel: {filename} with {len(all_items)} valves")

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Valve-Count": str(len(all_items)),
                "X-Rule-Id": rule_id,
                "X-Processing-Time": str(round(time.time() - start_time, 3))
            }
        )

    except ImportError as e:
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=f"Missing dependency: {e}. Install with: pip install openpyxl"
        )
    except Exception as e:
        logger.error(f"Excel export error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )
