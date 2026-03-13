"""
Dimension Parser — 데이터 모델
BearingDimension, BearingSpec 데이터 클래스 정의
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class BearingDimension:
    """베어링 치수 데이터 클래스"""
    raw_text: str = ""
    dimension_type: str = "unknown"
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    diameter: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    value: Optional[float] = None
    tolerance: Optional[str] = None
    tolerance_upper: Optional[float] = None
    tolerance_lower: Optional[float] = None
    fit_class: Optional[str] = None
    thread_pitch: Optional[float] = None  # 나사 피치 (M10×1.5의 1.5)
    unit: str = "mm"
    confidence: float = 1.0
    bbox: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class BearingSpec:
    """종합 베어링 사양"""
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    bore_diameter: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
