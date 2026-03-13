"""
테크로스 (techcross) P&ID 도면 파싱 Router
도면 유형: P&ID (BWMS/ECS 선박 설비)

엔드포인트:
  POST /api/v1/techcross/titleblock  — 표제란 파싱
  POST /api/v1/techcross/partslist   — Equipment List 파싱
  POST /api/v1/techcross/equipment   — 장비 태그 추출
  POST /api/v1/techcross/valves      — 밸브 태그 추출

생성일: 2026-03-12, 업데이트: 2026-03-13
"""

import os
import logging
import time
import httpx
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.techcross_parser import get_parser

logger = logging.getLogger(__name__)
router = APIRouter()

EDOCR2_URL = os.getenv("EDOCR2_URL", "http://edocr2-v2-api:5002")


# =====================
# Response Models
# =====================

class TitleBlockResponse(BaseModel):
    success: bool
    customer_id: str = "techcross"
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    system: Optional[str] = None
    ship_no: Optional[str] = None
    class_society: Optional[str] = None
    processing_time: float = 0.0
    error: Optional[str] = None


class PartsListResponse(BaseModel):
    success: bool
    customer_id: str = "techcross"
    items: List[Dict[str, Any]] = []
    total_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None


class EquipmentResponse(BaseModel):
    success: bool
    customer_id: str = "techcross"
    equipment: List[Dict[str, Any]] = []
    total_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None


class ValveResponse(BaseModel):
    success: bool
    customer_id: str = "techcross"
    valves: List[Dict[str, Any]] = []
    total_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None


# =====================
# OCR Helper
# =====================

async def _call_edocr2(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    """eDOCr2 OCR 서비스 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{EDOCR2_URL}/api/v1/process",
            files={"file": (filename, image_bytes, "image/png")},
        )
        response.raise_for_status()
        return response.json()


def _extract_ocr_texts(ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """OCR 결과에서 텍스트 + confidence 목록 추출"""
    texts: List[Dict[str, Any]] = []
    data = ocr_result.get("data", {})

    # regions 구조
    for region in data.get("regions", []):
        for text_item in region.get("texts", []):
            text = text_item.get("text", "").strip()
            if text:
                texts.append({
                    "text": text,
                    "confidence": text_item.get("confidence", 0.0),
                })

    # flat texts 구조 (fallback)
    if not texts:
        for item in data.get("texts", []):
            if isinstance(item, dict):
                text = item.get("text", "").strip()
                conf = item.get("confidence", 0.0)
            else:
                text = str(item).strip()
                conf = 0.0
            if text:
                texts.append({"text": text, "confidence": conf})

    return texts


def _texts_to_string(texts: List[Dict[str, Any]]) -> str:
    """텍스트 목록을 단일 문자열로 결합"""
    return "\n".join(t["text"] for t in texts)


# =====================
# Endpoints
# =====================

@router.post(
    "/api/v1/techcross/titleblock",
    response_model=TitleBlockResponse,
    summary="테크로스 P&ID 표제란 파싱",
    tags=["techcross"],
)
async def parse_titleblock(file: UploadFile = File(..., description="P&ID 도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_texts = _extract_ocr_texts(ocr_result)
        ocr_text = _texts_to_string(ocr_texts)

        parser = get_parser()
        parsed = parser.parse_title_block(ocr_text)

        return TitleBlockResponse(
            success=True,
            processing_time=round(time.time() - start, 3),
            **{k: v for k, v in parsed.items() if k in TitleBlockResponse.model_fields},
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        logger.warning(f"titleblock parsing failed: {e}")
        return TitleBlockResponse(
            success=False,
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/techcross/partslist",
    response_model=PartsListResponse,
    summary="테크로스 Equipment List 파싱",
    tags=["techcross"],
)
async def parse_partslist(file: UploadFile = File(..., description="P&ID 도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        table_data = ocr_result.get("data", {}).get("tables", None)
        ocr_text = _texts_to_string(_extract_ocr_texts(ocr_result))

        parser = get_parser()
        items = parser.parse_parts_list(table_data=table_data, ocr_text=ocr_text)

        return PartsListResponse(
            success=True,
            items=items,
            total_count=len(items),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        logger.warning(f"partslist parsing failed: {e}")
        return PartsListResponse(
            success=False,
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/techcross/equipment",
    response_model=EquipmentResponse,
    summary="테크로스 P&ID 장비 태그 추출",
    tags=["techcross"],
)
async def extract_equipment(file: UploadFile = File(..., description="P&ID 도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_texts = _extract_ocr_texts(ocr_result)

        parser = get_parser()
        equipment = parser.extract_equipment(ocr_texts)

        return EquipmentResponse(
            success=True,
            equipment=equipment,
            total_count=len(equipment),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        logger.warning(f"equipment extraction failed: {e}")
        return EquipmentResponse(
            success=False,
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/techcross/valves",
    response_model=ValveResponse,
    summary="테크로스 P&ID 밸브 태그 추출",
    tags=["techcross"],
)
async def extract_valves(file: UploadFile = File(..., description="P&ID 도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_texts = _extract_ocr_texts(ocr_result)

        parser = get_parser()
        valves = parser.extract_valves(ocr_texts)

        return ValveResponse(
            success=True,
            valves=valves,
            total_count=len(valves),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        logger.warning(f"valve extraction failed: {e}")
        return ValveResponse(
            success=False,
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )
