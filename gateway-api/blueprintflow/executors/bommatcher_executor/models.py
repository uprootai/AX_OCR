"""
BOM Matcher — 데이터 모델
BOMEntry, DrawingInfo 데이터클래스 정의
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class BOMEntry:
    """BOM 항목"""
    item_no: int
    part_no: str
    part_name: str
    material: str
    quantity: int
    dimensions: Optional[Dict[str, Any]] = None
    tolerances: Optional[List[str]] = None
    match_confidence: float = 1.0
    source: str = "partslist"


@dataclass
class DrawingInfo:
    """도면 메타 정보"""
    drawing_number: str
    revision: str
    title: str
    base_material: Optional[str] = None
    date: Optional[str] = None
    scale: Optional[str] = None
