"""
테크로스 (techcross) 파싱 Router
도면 유형: pid — P&ID 공정배관계장도

엔드포인트:
  POST /api/v1/techcross/titleblock
  POST /api/v1/techcross/partslist
  POST /api/v1/techcross/dimensions

생성일: 2026-03-12
"""

import logging
import time
import httpx
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.techcross_parser import get_parser

logger = logging.getLogger(__name__)
router = APIRouter()

EDOCR2_URL = "http://edocr2-v2-api:5002"


class TitleBlockResponse(BaseModel):
    success: bool
    customer_id: str
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    part_name: Optional[str] = None
    material: Optional[str] = None
    drawn_by: Optional[str] = None
    drawn_date: Optional[str] = None
    approved_by: Optional[str] = None
    scale: Optional[str] = None
    raw_fields: Dict[str, Any] = {}
    processing_time: float = 0.0
    error: Optional[str] = None


class PartsListResponse(BaseModel):
    success: bool
    customer_id: str
    items: List[Dict[str, Any]] = []
    total_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None


class DimensionsResponse(BaseModel):
    success: bool
    customer_id: str
    dimensions: List[Dict[str, Any]] = []
    total_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None


async def _call_edocr2(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{EDOCR2_URL}/api/v1/process",
            files={"file": (filename, image_bytes, "image/png")},
        )
        response.raise_for_status()
        return response.json()


def _extract_ocr_text(ocr_result: Dict[str, Any]) -> str:
    texts = []
    data = ocr_result.get("data", {})
    for region in data.get("regions", []):
        for text_item in region.get("texts", []):
            text = text_item.get("text", "").strip()
            if text:
                texts.append(text)
    if not texts:
        for item in data.get("texts", []):
            text = item.get("text", "").strip() if isinstance(item, dict) else str(item).strip()
            if text:
                texts.append(text)
    return "\n".join(texts)


@router.post(
    "/api/v1/techcross/titleblock",
    response_model=TitleBlockResponse,
    summary="테크로스 표제란 파싱",
    tags=["techcross"],
)
async def parse_titleblock(file: UploadFile = File(..., description="도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_text = _extract_ocr_text(ocr_result)
        parser = get_parser()
        parsed = parser.parse_title_block(ocr_text)
        return TitleBlockResponse(
            success=True,
            customer_id="techcross",
            processing_time=round(time.time() - start, 3),
            **{k: v for k, v in parsed.items() if k in TitleBlockResponse.model_fields},
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        return TitleBlockResponse(
            success=False,
            customer_id="techcross",
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/techcross/partslist",
    response_model=PartsListResponse,
    summary="테크로스 부품 목록 파싱",
    tags=["techcross"],
)
async def parse_partslist(file: UploadFile = File(..., description="도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_text = _extract_ocr_text(ocr_result)
        table_data = ocr_result.get("data", {}).get("tables", None)
        parser = get_parser()
        items = parser.parse_parts_list(table_data=table_data, ocr_text=ocr_text)
        return PartsListResponse(
            success=True,
            customer_id="techcross",
            items=items,
            total_count=len(items),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        return PartsListResponse(
            success=False,
            customer_id="techcross",
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/techcross/dimensions",
    response_model=DimensionsResponse,
    summary="테크로스 치수 추출",
    tags=["techcross"],
)
async def extract_dimensions_endpoint(file: UploadFile = File(..., description="도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_text = _extract_ocr_text(ocr_result)
        parser = get_parser()
        dimensions = parser.extract_dimensions(ocr_text)
        return DimensionsResponse(
            success=True,
            customer_id="techcross",
            dimensions=dimensions,
            total_count=len(dimensions),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {e}")
    except Exception as e:
        return DimensionsResponse(
            success=False,
            customer_id="techcross",
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )
