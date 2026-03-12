"""
Customer API Scaffolding Templates
create_customer_api.py가 사용하는 파일 생성 템플릿 모음

생성일: auto-generated
"""

# =====================
# 템플릿: Parser
# =====================

PARSER_TEMPLATE = '''"""
{customer_name} ({customer_id}) 도면 파서
도면 유형: {drawing_type} — {drawing_type_desc}

생성일: {created_at}
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# =====================
# 데이터 모델
# =====================

@dataclass
class TitleBlockData:
    """표제란 파싱 결과"""
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    part_name: Optional[str] = None
    material: Optional[str] = None
    drawn_by: Optional[str] = None
    drawn_date: Optional[str] = None
    approved_by: Optional[str] = None
    scale: Optional[str] = None
    sheet: Optional[str] = None
    raw_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class PartsListItem:
    """부품 목록 항목"""
    item_no: Optional[str] = None
    description: Optional[str] = None
    material: Optional[str] = None
    quantity: Optional[int] = None
    part_number: Optional[str] = None
    remarks: Optional[str] = None


# =====================
# 파싱 패턴 (고객별 커스터마이징)
# =====================

# @AX:ANCHOR — {customer_id} 도면 번호 패턴
DRAWING_NUMBER_PATTERNS = [
    # TODO: {customer_name} 도면 번호 패턴으로 교체
    r"[A-Z]{{2}}\\d{{5,8}}",
    r"\\d{{4}}-\\d{{4}}",
]

REVISION_PATTERNS = [
    r"REV[.\\s]*([A-Z])",
    r"Rev[.\\s]*([A-Z0-9]+)",
    # TODO: {customer_name} 리비전 패턴 추가
]

MATERIAL_PATTERNS = [
    r"S[A-Z]\\d{{2,3}}[A-Z]?",
    r"ASTM\\s*[AB]\\d+",
    # TODO: {customer_name} 자재 코드 패턴 추가
]


# =====================
# Title Block 파싱
# =====================

def parse_title_block(ocr_text: str, raw_texts: Optional[List[str]] = None) -> TitleBlockData:
    """표제란 파싱"""
    result = TitleBlockData()
    if not ocr_text:
        return result
    result.drawing_number = _extract_drawing_number(ocr_text)
    result.revision = _extract_revision(ocr_text)
    result.material = _extract_material(ocr_text)
    # TODO: {customer_name} 특화 필드 추출 로직 구현
    return result


def _extract_drawing_number(text: str) -> Optional[str]:
    for pattern in DRAWING_NUMBER_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _extract_revision(text: str) -> Optional[str]:
    for pattern in REVISION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            return groups[0] if groups else match.group(0)
    return None


def _extract_material(text: str) -> Optional[str]:
    for pattern in MATERIAL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


# =====================
# Parts List 파싱
# =====================

def parse_parts_list(
    table_data: Optional[List[Dict[str, Any]]] = None,
    ocr_text: Optional[str] = None,
) -> List[PartsListItem]:
    """부품 목록 파싱"""
    if table_data:
        return _parse_from_table(table_data)
    if ocr_text:
        return _parse_from_ocr(ocr_text)
    return []


def _parse_from_table(table_data: List[Dict[str, Any]]) -> List[PartsListItem]:
    items = []
    for row in table_data:
        # TODO: {customer_name} 테이블 컬럼 매핑으로 교체
        item = PartsListItem(
            item_no=row.get("NO") or row.get("ITEM") or row.get("no"),
            description=row.get("DESCRIPTION") or row.get("DESC") or row.get("description"),
            material=row.get("MATERIAL") or row.get("MAT") or row.get("material"),
            quantity=_safe_int(row.get("QTY") or row.get("qty") or row.get("QUANTITY")),
            part_number=row.get("PART_NO") or row.get("P/N") or row.get("part_no"),
        )
        items.append(item)
    return items


def _parse_from_ocr(ocr_text: str) -> List[PartsListItem]:
    # TODO: {customer_name} OCR 폴백 파싱 구현
    logger.warning("OCR fallback parsing not yet implemented for {customer_id}")
    return []


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


# =====================
# Dimensions 파싱
# =====================

def extract_dimensions(ocr_text: str) -> List[Dict[str, Any]]:
    """치수 정보 추출"""
    dimensions = []
    mm_pattern = r"(\\d+(?:\\.\\d+)?)\\s*(?:mm|MM)"
    for match in re.finditer(mm_pattern, ocr_text):
        dimensions.append({{
            "value": float(match.group(1)),
            "unit": "mm",
            "tolerance": None,
            "type": "linear",
            "raw": match.group(0),
        }})
    tolerance_pattern = r"(\\d+(?:\\.\\d+)?)\\s*([+-]\\d+(?:\\.\\d+)?)"
    for match in re.finditer(tolerance_pattern, ocr_text):
        dimensions.append({{
            "value": float(match.group(1)),
            "unit": "mm",
            "tolerance": match.group(2),
            "type": "toleranced",
            "raw": match.group(0),
        }})
    # TODO: {customer_name} 특화 치수 패턴 추가
    return dimensions


# =====================
# 메인 파서 클래스
# =====================

class {pascal_id}Parser:
    """
    {customer_name} 도면 파서
    도면 유형: {drawing_type}
    """
    DRAWING_TYPE = "{drawing_type}"
    CUSTOMER_ID = "{customer_id}"
    CUSTOMER_NAME = "{customer_name}"

    def __init__(self):
        logger.info(f"Initializing {{self.CUSTOMER_NAME}} parser (type: {{self.DRAWING_TYPE}})")

    def parse_title_block(self, ocr_text: str, raw_texts=None) -> Dict[str, Any]:
        result = parse_title_block(ocr_text, raw_texts)
        return {{
            "drawing_number": result.drawing_number,
            "revision": result.revision,
            "part_name": result.part_name,
            "material": result.material,
            "drawn_by": result.drawn_by,
            "drawn_date": result.drawn_date,
            "approved_by": result.approved_by,
            "scale": result.scale,
            "sheet": result.sheet,
        }}

    def parse_parts_list(self, table_data=None, ocr_text=None) -> List[Dict[str, Any]]:
        items = parse_parts_list(table_data, ocr_text)
        return [
            {{
                "item_no": i.item_no,
                "description": i.description,
                "material": i.material,
                "quantity": i.quantity,
                "part_number": i.part_number,
                "remarks": i.remarks,
            }}
            for i in items
        ]

    def extract_dimensions(self, ocr_text: str) -> List[Dict[str, Any]]:
        return extract_dimensions(ocr_text)


_parser_instance = None


def get_parser() -> {pascal_id}Parser:
    """파서 인스턴스 반환 (싱글톤)"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = {pascal_id}Parser()
    return _parser_instance
'''


# =====================
# 템플릿: Router
# =====================

ROUTER_TEMPLATE = '''"""
{customer_name} ({customer_id}) 파싱 Router
도면 유형: {drawing_type} — {drawing_type_desc}

엔드포인트:
  POST /api/v1/{customer_id}/titleblock
  POST /api/v1/{customer_id}/partslist
  POST /api/v1/{customer_id}/dimensions

생성일: {created_at}
"""

import logging
import time
import httpx
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.{customer_id}_parser import get_parser

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
    raw_fields: Dict[str, Any] = {{}}
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
            f"{{EDOCR2_URL}}/api/v1/process",
            files={{"file": (filename, image_bytes, "image/png")}},
        )
        response.raise_for_status()
        return response.json()


def _extract_ocr_text(ocr_result: Dict[str, Any]) -> str:
    texts = []
    data = ocr_result.get("data", {{}})
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
    return "\\n".join(texts)


@router.post(
    "/api/v1/{customer_id}/titleblock",
    response_model=TitleBlockResponse,
    summary="{customer_name} 표제란 파싱",
    tags=["{customer_id}"],
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
            customer_id="{customer_id}",
            processing_time=round(time.time() - start, 3),
            **{{k: v for k, v in parsed.items() if k in TitleBlockResponse.model_fields}},
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {{e}}")
    except Exception as e:
        return TitleBlockResponse(
            success=False,
            customer_id="{customer_id}",
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/{customer_id}/partslist",
    response_model=PartsListResponse,
    summary="{customer_name} 부품 목록 파싱",
    tags=["{customer_id}"],
)
async def parse_partslist(file: UploadFile = File(..., description="도면 이미지")):
    start = time.time()
    try:
        image_bytes = await file.read()
        ocr_result = await _call_edocr2(image_bytes, file.filename or "drawing.png")
        ocr_text = _extract_ocr_text(ocr_result)
        table_data = ocr_result.get("data", {{}}).get("tables", None)
        parser = get_parser()
        items = parser.parse_parts_list(table_data=table_data, ocr_text=ocr_text)
        return PartsListResponse(
            success=True,
            customer_id="{customer_id}",
            items=items,
            total_count=len(items),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {{e}}")
    except Exception as e:
        return PartsListResponse(
            success=False,
            customer_id="{customer_id}",
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )


@router.post(
    "/api/v1/{customer_id}/dimensions",
    response_model=DimensionsResponse,
    summary="{customer_name} 치수 추출",
    tags=["{customer_id}"],
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
            customer_id="{customer_id}",
            dimensions=dimensions,
            total_count=len(dimensions),
            processing_time=round(time.time() - start, 3),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OCR service error: {{e}}")
    except Exception as e:
        return DimensionsResponse(
            success=False,
            customer_id="{customer_id}",
            processing_time=round(time.time() - start, 3),
            error=str(e),
        )
'''


# =====================
# 템플릿: API Spec (YAML)
# =====================

SPEC_TEMPLATE = '''# {customer_name} ({customer_id}) API Specification
# 도면 유형: {drawing_type} — {drawing_type_desc}
# 생성일: {created_at}

apiVersion: v1
kind: CustomerAPISpec

metadata:
  id: {customer_id}
  name: "{customer_name} Parser"
  version: 1.0.0
  drawing_type: {drawing_type}
  description: "{customer_name} 도면 파싱 API ({drawing_type_desc})"
  author: AX Team
  created_at: "{created_at}"
  tags:
{tags_yaml}

server:
  gateway_url: http://localhost:8000
  prefix: /api/v1/{customer_id}
  timeout: 60

endpoints:
  - path: /titleblock
    method: POST
    summary: "표제란 파싱"
    content_type: multipart/form-data
    inputs:
      - name: file
        type: file
        required: true
        description: "도면 이미지 (PNG/JPG)"
    outputs:
      drawing_number: string
      revision: string
      part_name: string
      material: string
      drawn_by: string
      drawn_date: string

  - path: /partslist
    method: POST
    summary: "부품 목록 파싱"
    content_type: multipart/form-data
    inputs:
      - name: file
        type: file
        required: true
    outputs:
      items: array
      total_count: integer

  - path: /dimensions
    method: POST
    summary: "치수 추출"
    content_type: multipart/form-data
    inputs:
      - name: file
        type: file
        required: true
    outputs:
      dimensions: array
      total_count: integer

parsing_profile:
  drawing_number_pattern: "TODO: {customer_name} 도면 번호 패턴"
  revision_pattern: "TODO: {customer_name} 리비전 패턴"
  table_headers: []

port_mapping:
  gateway: 8000
  edocr2: 5002
  yolo: 5005
  table_detector: 5006
'''


# =====================
# 템플릿: Config
# =====================

CONFIG_TEMPLATE = '''"""
{customer_name} ({customer_id}) Customer Configuration
도면 유형: {drawing_type} — {drawing_type_desc}

생성일: {created_at}
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class {pascal_id}ParsingProfile:
    """
    {customer_name} 도면 파싱 프로파일
    @AX:TODO: 실제 {customer_name} 패턴으로 교체
    """
    profile_id: str = "{customer_id}"
    name: str = "{customer_name}"

    drawing_number_patterns: List[str] = field(default_factory=lambda: [
        r"[A-Z]{{2}}\\d{{5,8}}",
        r"\\d{{4}}-\\d{{4}}",
    ])
    revision_patterns: List[str] = field(default_factory=lambda: [
        r"REV[.\\s]*([A-Z])",
        r"Rev[.\\s]*([A-Z0-9]+)",
    ])
    material_patterns: List[str] = field(default_factory=lambda: [
        r"S[A-Z]\\d{{2,3}}[A-Z]?",
        r"ASTM\\s*[AB]\\d+",
    ])

    # @AX:TODO: 실제 헤더로 교체
    table_headers: List[str] = field(default_factory=lambda: [
        "NO", "DESCRIPTION", "MATERIAL", "QTY"
    ])
    column_mapping: Dict[str, str] = field(default_factory=lambda: {{
        "NO": "item_no",
        "DESCRIPTION": "description",
        "MATERIAL": "material",
        "QTY": "quantity",
    }})

    ocr_engine: str = "edocr2"
    drawing_type: str = "{drawing_type}"


@dataclass
class {pascal_id}PricingConfig:
    """
    {customer_name} 가격 설정
    @AX:WARN — 실제 계약 단가로 반드시 교체
    """
    customer_id: str = "{customer_id}"
    customer_name: str = "{customer_name}"

    base_rates: Dict[str, float] = field(default_factory=lambda: {{
        "machining_per_hour": 0.0,
        "material_markup": 0.0,
        "setup_fee": 0.0,
    }})

    lead_times: Dict[str, int] = field(default_factory=lambda: {{
        "standard": 14,
        "express": 7,
        "urgent": 3,
    }})

    min_order_qty: int = 1
    currency: str = "KRW"


@dataclass
class {pascal_id}Config:
    """
    {customer_name} 통합 설정 — 파싱 + 가격 + 메타데이터
    """
    customer_id: str = "{customer_id}"
    customer_name: str = "{customer_name}"
    drawing_type: str = "{drawing_type}"
    is_active: bool = True

    parsing: {pascal_id}ParsingProfile = field(default_factory={pascal_id}ParsingProfile)
    pricing: {pascal_id}PricingConfig = field(default_factory={pascal_id}PricingConfig)

    model_pipeline: List[str] = field(default_factory=lambda: {model_pipeline})


_config_instance: Optional[{pascal_id}Config] = None


def get_config() -> {pascal_id}Config:
    """설정 인스턴스 반환 (싱글톤)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = {pascal_id}Config()
        logger.info(
            f"Loaded config for {{_config_instance.customer_name}} "
            f"(type: {{_config_instance.drawing_type}})"
        )
    return _config_instance
'''
