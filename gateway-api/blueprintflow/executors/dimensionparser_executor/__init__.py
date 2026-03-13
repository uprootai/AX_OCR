"""
Dimension Parser Executor 패키지
베어링 도면 치수를 구조화된 형태로 파싱

지원 패턴:
- OD670×ID440 → {outer_diameter: 670, inner_diameter: 440}
- 1100×ID680×200L → {width: 1100, inner_diameter: 680, length: 200}
- Ø25H7 → {diameter: 25, tolerance: "H7"}
- 50.0±0.1 → {value: 50.0, tolerance: "±0.1"}
- ⌀25 → {diameter: 25, symbol: "⌀"}
"""
from .models import BearingDimension, BearingSpec
from .patterns import DIMENSION_PATTERNS, GDT_PATTERNS
from .executor import DimensionParserExecutor

__all__ = [
    "DimensionParserExecutor",
    "BearingDimension",
    "BearingSpec",
    "DIMENSION_PATTERNS",
    "GDT_PATTERNS",
]
