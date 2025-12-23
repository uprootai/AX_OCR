"""Line Detection Schemas - 선 검출 스키마

선 검출 결과 및 치수-심볼 관계 분석을 위한 스키마
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class LineType(str, Enum):
    """선 유형"""
    PROCESS = "process"          # 공정 배관
    COOLING = "cooling"          # 냉각 배관
    STEAM = "steam"              # 증기 배관
    SIGNAL = "signal"            # 신호선
    ELECTRICAL = "electrical"    # 전기 배선
    DIMENSION = "dimension"      # 치수선
    EXTENSION = "extension"      # 연장선 (치수)
    LEADER = "leader"            # 지시선
    UNKNOWN = "unknown"


class LineStyle(str, Enum):
    """선 스타일"""
    SOLID = "solid"              # 실선
    DASHED = "dashed"            # 점선
    DOTTED = "dotted"            # 점점선
    CHAIN = "chain"              # 1점 쇄선
    DOUBLE_CHAIN = "double_chain"  # 2점 쇄선
    UNKNOWN = "unknown"


class Point(BaseModel):
    """2D 점 좌표"""
    x: float
    y: float


class Line(BaseModel):
    """검출된 선"""
    id: str
    start: Point
    end: Point
    length: float
    angle: float                         # 라디안
    line_type: LineType = LineType.UNKNOWN
    line_style: LineStyle = LineStyle.UNKNOWN
    color: Optional[str] = None          # 검출된 색상 (hex)
    confidence: float = 1.0
    thickness: Optional[float] = None    # 선 두께 (픽셀)

    # 연결 정보
    connected_to: List[str] = []         # 연결된 다른 선 ID
    intersections: List[str] = []        # 교차점 ID


class Intersection(BaseModel):
    """교차점"""
    id: str
    point: Point
    line_ids: List[str]                  # 교차하는 선 ID들
    intersection_type: Optional[str] = None  # T, X, L 등


class DimensionLineRelation(BaseModel):
    """치수선과 심볼 간의 관계"""
    dimension_id: str                    # 치수 ID
    target_type: str                     # 'symbol', 'line', 'edge' 등
    target_id: Optional[str] = None      # 대상 ID
    relation_type: str                   # 'distance', 'diameter', 'angle' 등
    direction: Optional[str] = None      # 'horizontal', 'vertical', 'diagonal'
    confidence: float = 0.5


class LineDetectionResult(BaseModel):
    """선 검출 결과"""
    lines: List[Line]
    intersections: List[Intersection]
    statistics: Dict[str, Any]
    processing_time_ms: float
    image_width: int
    image_height: int
    visualization_base64: Optional[str] = None


class LineDetectionConfig(BaseModel):
    """선 검출 설정"""
    method: str = "lsd"                  # 'lsd', 'hough', 'combined'
    merge_lines: bool = True
    classify_types: bool = True
    classify_colors: bool = True
    classify_styles: bool = True
    find_intersections: bool = True
    visualize: bool = True
    min_length: int = 0
    max_lines: int = 0


class DimensionSymbolLinkRequest(BaseModel):
    """치수-심볼 연결 요청"""
    session_id: str
    dimension_ids: List[str]
    symbol_ids: List[str]
    auto_link: bool = True               # 자동으로 가장 가까운 심볼에 연결


class DimensionSymbolLink(BaseModel):
    """치수-심볼 연결 결과"""
    dimension_id: str
    symbol_id: Optional[str]
    link_type: str                       # 'auto', 'manual', 'inferred'
    distance: float                      # 픽셀 거리
    confidence: float
