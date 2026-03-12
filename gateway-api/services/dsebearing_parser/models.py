"""
DSE Bearing Parser — Data Models

TitleBlockData, PartsListItem 데이터클래스 정의
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class TitleBlockData:
    """Title Block 데이터"""
    drawing_number: str = ""
    revision: str = ""
    part_name: str = ""
    material: str = ""
    date: str = ""
    size: str = ""
    scale: str = ""
    sheet: str = ""
    unit: str = "mm"
    company: str = ""
    raw_texts: List[str] = None

    def __post_init__(self):
        if self.raw_texts is None:
            self.raw_texts = []

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items()}


@dataclass
class PartsListItem:
    """Parts List 항목"""
    no: str = ""
    description: str = ""
    material: str = ""
    size_dwg_no: str = ""
    qty: int = 1
    remark: str = ""
    weight: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}
