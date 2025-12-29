"""
Generic Equipment Router
/api/v1/equipment/* 엔드포인트

범용 장비 검출 API (프로파일 기반)
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
    detect_equipment,
    get_equipment_summary,
    check_profile_context,
    generate_equipment_list_excel,
    get_available_profiles,
    get_profile_equipment_types,
    EQUIPMENT_PROFILES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/equipment", tags=["Equipment"])

# Configuration
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
# Endpoints
# =====================

@router.get("/profiles")
async def list_equipment_profiles():
    """
    사용 가능한 장비 프로파일 목록 조회

    프로파일: 특정 산업/분야에 맞는 장비 패턴 세트
    - bwms: 선박 평형수 처리 시스템
    - hvac: 공조 시스템
    - process: 일반 공정
    """
    return {
        "success": True,
        "data": {
            "profiles": get_available_profiles(),
            "total": len(EQUIPMENT_PROFILES)
        }
    }


@router.get("/profiles/{profile_id}")
async def get_equipment_profile_detail(profile_id: str):
    """
    특정 프로파일 상세 정보 조회
    """
    profile = EQUIPMENT_PROFILES.get(profile_id)
    if not profile:
        return {
            "success": False,
            "error": f"Profile '{profile_id}' not found. Available: {list(EQUIPMENT_PROFILES.keys())}"
        }

    return {
        "success": True,
        "data": {
            "id": profile_id,
            "name": profile['name'],
            "name_ko": profile['name_ko'],
            "description": profile['description'],
            "context_keywords": profile.get('context_keywords', []),
            "equipment_types": get_profile_equipment_types(profile_id),
            "equipment_count": len(profile['equipment'])
        }
    }


@router.post("/detect")
async def detect_equipment_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    profile_id: str = Form(default="bwms", description="장비 프로파일 (bwms/hvac/process)"),
    language: str = Form(default="en", description="OCR 언어 (en/ko)")
):
    """
    장비 태그 검출 API (범용)

    선택한 프로파일에 따라 P&ID 도면에서 장비 태그를 자동 인식합니다.

    Parameters:
    - profile_id: 사용할 장비 프로파일 (bwms, hvac, process)
    - language: OCR 언어 설정
    """
    start_time = time.time()

    try:
        # 프로파일 유효성 검사
        if profile_id not in EQUIPMENT_PROFILES:
            return ProcessResponse(
                success=False,
                data={"available_profiles": list(EQUIPMENT_PROFILES.keys())},
                processing_time=time.time() - start_time,
                error=f"Unknown profile: {profile_id}"
            )

        # 이미지 읽기
        image_bytes = await file.read()

        # PaddleOCR로 텍스트 추출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, image_bytes, file.content_type)}
            data = {"language": language}
            response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"OCR API error: {response.status_code}"
            )

        ocr_result = response.json()
        ocr_texts = ocr_result.get('detections', [])
        if not ocr_texts:
            ocr_texts = ocr_result.get('texts', [])

        logger.info(f"OCR detected {len(ocr_texts)} texts")

        # 프로파일 컨텍스트 확인
        context_check = check_profile_context(ocr_texts, profile_id)

        # 장비 검출 (선택된 프로파일 사용)
        equipment = detect_equipment(ocr_texts, profile_id=profile_id)
        summary = get_equipment_summary(equipment) if equipment else {}

        processing_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            data={
                'equipment': equipment,
                'summary': summary,
                'profile': {
                    'id': profile_id,
                    'name': EQUIPMENT_PROFILES[profile_id]['name_ko']
                },
                'context_check': context_check,
                'ocr_count': len(ocr_texts)
            },
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Equipment detection error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


@router.post("/export-excel")
async def export_equipment_excel_endpoint(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    profile_id: str = Form(default="bwms", description="장비 프로파일"),
    project_name: str = Form(default="Unknown Project", description="프로젝트명"),
    drawing_no: str = Form(default="N/A", description="도면 번호"),
    language: str = Form(default="en", description="OCR 언어")
):
    """
    장비 목록 Excel 내보내기 API (범용)

    P&ID 도면에서 장비를 검출하고 Excel 파일로 출력합니다.

    Parameters:
    - profile_id: 사용할 장비 프로파일
    - project_name: Excel에 표시할 프로젝트명
    - drawing_no: 도면 번호
    """
    start_time = time.time()

    try:
        # 프로파일 유효성 검사
        if profile_id not in EQUIPMENT_PROFILES:
            return ProcessResponse(
                success=False,
                data={"available_profiles": list(EQUIPMENT_PROFILES.keys())},
                processing_time=time.time() - start_time,
                error=f"Unknown profile: {profile_id}"
            )

        # 이미지 읽기
        image_bytes = await file.read()

        # PaddleOCR로 텍스트 추출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, image_bytes, "image/png")}
            data = {"language": language}
            response = await client.post(PADDLEOCR_API_URL, files=files, data=data)

        if response.status_code != 200:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"OCR API error: {response.status_code}"
            )

        ocr_result = response.json()
        ocr_texts = ocr_result.get('detections', [])
        if not ocr_texts:
            ocr_texts = ocr_result.get('texts', [])

        # 장비 검출
        equipment = detect_equipment(ocr_texts, profile_id=profile_id)

        if not equipment:
            return ProcessResponse(
                success=False,
                data={},
                processing_time=time.time() - start_time,
                error=f"No equipment detected with profile '{profile_id}'"
            )

        # Excel 생성
        project_info = {
            'name': project_name,
            'drawing_no': drawing_no
        }

        excel_bytes = generate_equipment_list_excel(equipment, project_info, profile_id)

        # 파일명 생성
        profile_name = profile_id.upper()
        filename = f"{profile_name}_Equipment_List_{drawing_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Generated Excel: {filename} with {len(equipment)} equipment")

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Equipment-Count": str(len(equipment)),
                "X-Profile": profile_id,
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
