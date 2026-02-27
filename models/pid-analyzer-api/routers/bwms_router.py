"""
BWMS (Ballast Water Management System) Router
/api/v1/bwms/* 엔드포인트
"""

import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import Response
from pydantic import BaseModel
import httpx

from equipment_analyzer import (
    detect_bwms_equipment,
    get_bwms_equipment_summary,
    check_bwms_context,
    generate_bwms_equipment_list_excel,
    EQUIPMENT_PROFILES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bwms", tags=["BWMS"])

# Configuration — OCR Ensemble 우선, PaddleOCR 폴백 (Docker 네트워크 기본)
OCR_ENSEMBLE_API_URL = os.getenv("OCR_ENSEMBLE_API_URL", "http://ocr-ensemble-api:5011/api/v1/ocr")
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006/api/v1/ocr")


# =====================
# Schemas
# =====================

class ProcessResponse(BaseModel):
    success: bool
    data: Dict
    processing_time: float
    error: Optional[str] = None


# =====================
# OCR Helper
# =====================

async def _call_ocr_api(filename: str, image_bytes: bytes, content_type: str, language: str) -> list:
    """OCR Ensemble 우선 호출, 실패 시 PaddleOCR 폴백"""
    urls = [
        (OCR_ENSEMBLE_API_URL, "OCR Ensemble"),
        (PADDLEOCR_API_URL, "PaddleOCR"),
    ]
    for url, name in urls:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": (filename, image_bytes, content_type)}
                data = {"language": language}
                response = await client.post(url, files=files, data=data)

            if response.status_code != 200:
                logger.warning(f"{name} returned {response.status_code}, trying next")
                continue

            ocr_result = response.json() or {}
            # 여러 응답 형식 지원
            texts = (
                ocr_result.get('results', [])
                or ocr_result.get('detections', [])
                or ocr_result.get('texts', [])
            )
            if texts:
                logger.info(f"{name} returned {len(texts)} texts")
                return texts
            logger.warning(f"{name} returned 0 texts, trying next")
        except Exception as e:
            logger.warning(f"{name} error: {e}, trying next")
    return []


# =====================
# Endpoints
# =====================

@router.post("/detect-equipment")
async def detect_bwms_equipment_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    language: str = Form(default="en", description="OCR 언어 (en/ko)")
):
    """
    BWMS 장비 태그 검출 API

    P&ID 도면에서 BWMS 전용 장비(ECU, FMU, HGU 등)를 자동 인식합니다.
    """
    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()

        # OCR 텍스트 추출 (Ensemble 우선 → PaddleOCR 폴백)
        ocr_texts = await _call_ocr_api(file.filename, image_bytes, file.content_type, language)
        logger.info(f"OCR detected {len(ocr_texts)} texts")

        # BWMS 컨텍스트 확인
        bwms_context = check_bwms_context(ocr_texts)

        # BWMS 장비 검출
        equipment = detect_bwms_equipment(ocr_texts)
        summary = get_bwms_equipment_summary(equipment)

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                'equipment': equipment,
                'summary': summary,
                'bwms_context': bwms_context,
                'ocr_count': len(ocr_texts)
            },
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"BWMS detection error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/generate-equipment-list")
async def generate_bwms_equipment_list_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    project_name: str = Form(default="Unknown Project", description="프로젝트명"),
    hull_no: str = Form(default="N/A", description="선체 번호"),
    drawing_no: str = Form(default="N/A", description="도면 번호"),
    language: str = Form(default="en", description="OCR 언어")
):
    """
    BWMS Equipment List Excel 생성 API

    P&ID 도면에서 BWMS 장비를 검출하고 Excel 파일로 출력합니다.
    """
    start_time = time.time()

    try:
        # 이미지 읽기
        image_bytes = await file.read()

        # OCR 텍스트 추출 (Ensemble 우선 → PaddleOCR 폴백)
        ocr_texts = await _call_ocr_api(file.filename, image_bytes, "image/png", language)

        # BWMS 장비 검출
        equipment = detect_bwms_equipment(ocr_texts)

        if not equipment:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error="No BWMS equipment detected in the image"
            )

        # Excel 생성
        project_info = {
            'name': project_name,
            'hull_no': hull_no,
            'drawing_no': drawing_no
        }

        excel_bytes = generate_bwms_equipment_list_excel(equipment, project_info)

        # 파일명 생성
        filename = f"BWMS_Equipment_List_{hull_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Generated Excel: {filename} with {len(equipment)} equipment")

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Equipment-Count": str(len(equipment)),
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
        logger.error(f"Excel generation error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.get("/equipment-types")
async def get_bwms_equipment_types():
    """
    BWMS 장비 타입 목록 조회 (Legacy)

    지원하는 BWMS 장비 타입 및 설명을 반환합니다.
    새로운 API: /api/v1/equipment/profiles/bwms/types 사용 권장
    """
    bwms_profile = EQUIPMENT_PROFILES.get('bwms', {})
    bwms_equipment = bwms_profile.get('equipment', {})

    return {
        "success": True,
        "data": {
            "equipment_types": [
                {
                    "type": equip_type,
                    "name_ko": info["name_ko"],
                    "name_en": info["name_en"],
                    "description": info["description"],
                    "category": info["category"],
                    "pattern": info["pattern"]
                }
                for equip_type, info in bwms_equipment.items()
            ],
            "total_types": len(bwms_equipment)
        }
    }
