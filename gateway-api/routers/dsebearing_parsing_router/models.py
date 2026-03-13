"""
DSE Bearing Parsing — Pydantic response models
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """공통 에러 응답"""
    success: bool = False
    error_code: str
    message: str
    details: Dict[str, Any] = {}


class TitleBlockResponse(BaseModel):
    success: bool
    drawing_number: str
    revision: str
    part_name: str
    material: str
    date: str
    size: str = ""
    scale: str = ""
    sheet: str = ""
    company: str = ""
    raw_texts: List[str] = []
    confidence: float = 0.0


class PartsListItemResponse(BaseModel):
    no: str
    description: str
    material: str
    size_dwg_no: str = ""
    qty: int
    remark: str = ""
    weight: Optional[float] = None


class PartsListResponse(BaseModel):
    success: bool
    items: List[PartsListItemResponse]
    total_count: int
    confidence: float = 0.0


class DimensionItem(BaseModel):
    type: str
    value: Optional[float] = None
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    tolerance: Optional[str] = None
    upper_tolerance: Optional[float] = None
    lower_tolerance: Optional[float] = None
    unit: str = "mm"
    raw_text: str = ""


class DimensionParserResponse(BaseModel):
    success: bool
    dimensions: List[DimensionItem]
    gdt_symbols: List[str] = []
    confidence: float = 0.0


class BOMItem(BaseModel):
    no: str
    description: str
    material: str
    size_dwg_no: str = ""
    dimensions: List[DimensionItem] = []
    qty: int
    weight: Optional[float] = None


class BOMMatcherResponse(BaseModel):
    success: bool
    matched_items: List[BOMItem]
    unmatched_count: int
    match_confidence: float
