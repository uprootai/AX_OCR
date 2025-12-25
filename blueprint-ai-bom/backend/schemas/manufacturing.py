"""
Manufacturing Feature Schemas
중기 로드맵 기능 스키마 정의 (2025-12-24)

- 용접 기호 파싱 (welding_symbol_parsing)
- 표면 거칠기 파싱 (surface_roughness_parsing)
- 수량 추출 (quantity_extraction)
- 벌룬 번호 매칭 (balloon_matching)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# 용접 기호 파싱 (Welding Symbol Parsing)
# ============================================================

class WeldingType(str, Enum):
    """용접 타입"""
    FILLET = "fillet"  # 필렛 용접
    GROOVE = "groove"  # 그루브 용접
    PLUG = "plug"  # 플러그 용접
    SLOT = "slot"  # 슬롯 용접
    SPOT = "spot"  # 점 용접
    SEAM = "seam"  # 심 용접
    BACK = "back"  # 이면 용접
    SURFACING = "surfacing"  # 표면 용접
    FLANGE = "flange"  # 플랜지 용접
    UNKNOWN = "unknown"


class WeldingLocation(str, Enum):
    """용접 위치 (화살표 기준)"""
    ARROW_SIDE = "arrow_side"  # 화살표 쪽
    OTHER_SIDE = "other_side"  # 반대쪽
    BOTH_SIDES = "both_sides"  # 양쪽


class WeldingSymbol(BaseModel):
    """용접 기호 데이터"""
    id: str = Field(..., description="용접 기호 고유 ID")
    welding_type: WeldingType = Field(WeldingType.UNKNOWN, description="용접 타입")
    location: WeldingLocation = Field(WeldingLocation.ARROW_SIDE, description="용접 위치")

    # 치수 정보
    size: Optional[str] = Field(None, description="용접 크기 (예: 6mm)")
    length: Optional[str] = Field(None, description="용접 길이 (예: 50mm)")
    pitch: Optional[str] = Field(None, description="용접 피치 (예: 100mm)")
    depth: Optional[str] = Field(None, description="용접 깊이 (예: 3mm)")
    root_opening: Optional[str] = Field(None, description="루트 간격")
    groove_angle: Optional[str] = Field(None, description="그루브 각도")

    # 추가 정보
    field_weld: bool = Field(False, description="현장 용접 여부")
    all_around: bool = Field(False, description="전 둘레 용접 여부")
    contour: Optional[str] = Field(None, description="마감 형상 (flush, convex, concave)")
    process: Optional[str] = Field(None, description="용접 공정 (예: GTAW, SMAW)")

    # 위치 정보
    bbox: Optional[List[float]] = Field(None, description="바운딩 박스 [x1, y1, x2, y2]")
    confidence: float = Field(0.0, description="검출 신뢰도")

    # 원본 텍스트
    raw_text: Optional[str] = Field(None, description="원본 텍스트")


class WeldingParsingResult(BaseModel):
    """용접 기호 파싱 결과"""
    session_id: str
    welding_symbols: List[WeldingSymbol] = Field(default_factory=list)
    total_count: int = Field(0, description="총 용접 기호 수")
    by_type: Dict[str, int] = Field(default_factory=dict, description="타입별 개수")
    processing_time_ms: float = Field(0.0)


# ============================================================
# 표면 거칠기 파싱 (Surface Roughness Parsing)
# ============================================================

class RoughnessType(str, Enum):
    """거칠기 타입"""
    RA = "Ra"  # 산술 평균 거칠기
    RZ = "Rz"  # 최대 높이 거칠기
    RMAX = "Rmax"  # 최대 거칠기
    RQ = "Rq"  # 제곱 평균 거칠기
    RT = "Rt"  # 총 높이
    UNKNOWN = "unknown"


class MachiningMethod(str, Enum):
    """가공 방법"""
    TURNING = "turning"  # 선삭
    MILLING = "milling"  # 밀링
    GRINDING = "grinding"  # 연삭
    LAPPING = "lapping"  # 래핑
    HONING = "honing"  # 호닝
    POLISHING = "polishing"  # 연마
    CASTING = "casting"  # 주조
    FORGING = "forging"  # 단조
    ANY = "any"  # 무관
    UNKNOWN = "unknown"


class LayDirection(str, Enum):
    """가공 방향"""
    PARALLEL = "parallel"  # 평행 =
    PERPENDICULAR = "perpendicular"  # 수직 ⊥
    CROSSED = "crossed"  # 교차 X
    MULTIDIRECTIONAL = "multidirectional"  # 다방향 M
    CIRCULAR = "circular"  # 원형 C
    RADIAL = "radial"  # 방사형 R
    UNKNOWN = "unknown"


class SurfaceRoughness(BaseModel):
    """표면 거칠기 데이터"""
    id: str = Field(..., description="거칠기 기호 고유 ID")
    roughness_type: RoughnessType = Field(RoughnessType.RA, description="거칠기 타입")
    value: Optional[float] = Field(None, description="거칠기 값")
    unit: str = Field("μm", description="단위")

    # 추가 파라미터
    upper_limit: Optional[float] = Field(None, description="상한값")
    lower_limit: Optional[float] = Field(None, description="하한값")
    sampling_length: Optional[float] = Field(None, description="샘플링 길이")

    # 가공 정보
    machining_method: MachiningMethod = Field(MachiningMethod.UNKNOWN, description="가공 방법")
    machining_allowance: Optional[float] = Field(None, description="가공 여유")
    lay_direction: LayDirection = Field(LayDirection.UNKNOWN, description="가공 방향")

    # 위치 정보
    bbox: Optional[List[float]] = Field(None, description="바운딩 박스 [x1, y1, x2, y2]")
    confidence: float = Field(0.0, description="검출 신뢰도")

    # 원본 텍스트
    raw_text: Optional[str] = Field(None, description="원본 텍스트")


class SurfaceRoughnessResult(BaseModel):
    """표면 거칠기 파싱 결과"""
    session_id: str
    roughness_symbols: List[SurfaceRoughness] = Field(default_factory=list)
    total_count: int = Field(0, description="총 거칠기 기호 수")
    by_type: Dict[str, int] = Field(default_factory=dict, description="타입별 개수")
    processing_time_ms: float = Field(0.0)


# ============================================================
# 수량 추출 (Quantity Extraction)
# ============================================================

class QuantitySource(str, Enum):
    """수량 출처"""
    BALLOON = "balloon"  # 벌룬 옆
    TABLE = "table"  # BOM 테이블
    NOTE = "note"  # 노트/주석
    INLINE = "inline"  # 인라인 텍스트
    UNKNOWN = "unknown"


class QuantityItem(BaseModel):
    """수량 정보"""
    id: str = Field(..., description="수량 항목 고유 ID")
    quantity: int = Field(1, description="수량")
    unit: Optional[str] = Field(None, description="단위 (EA, SET, ASSY 등)")

    # 연결 정보
    part_number: Optional[str] = Field(None, description="연결된 부품번호")
    balloon_number: Optional[str] = Field(None, description="연결된 벌룬 번호")
    symbol_id: Optional[str] = Field(None, description="연결된 심볼 ID")

    # 출처 정보
    source: QuantitySource = Field(QuantitySource.UNKNOWN, description="수량 출처")
    pattern_matched: Optional[str] = Field(None, description="매칭된 패턴 (예: QTY: 4)")

    # 위치 정보
    bbox: Optional[List[float]] = Field(None, description="바운딩 박스 [x1, y1, x2, y2]")
    confidence: float = Field(0.0, description="추출 신뢰도")

    # 원본 텍스트
    raw_text: Optional[str] = Field(None, description="원본 텍스트")


class QuantityExtractionResult(BaseModel):
    """수량 추출 결과"""
    session_id: str
    quantities: List[QuantityItem] = Field(default_factory=list)
    total_items: int = Field(0, description="총 수량 항목 수")
    total_quantity: int = Field(0, description="총 부품 수량 합계")
    by_source: Dict[str, int] = Field(default_factory=dict, description="출처별 개수")
    processing_time_ms: float = Field(0.0)


# ============================================================
# 벌룬 번호 매칭 (Balloon Matching)
# ============================================================

class BalloonShape(str, Enum):
    """벌룬 형태"""
    CIRCLE = "circle"  # 원형
    TRIANGLE = "triangle"  # 삼각형
    SQUARE = "square"  # 사각형
    HEXAGON = "hexagon"  # 육각형
    DIAMOND = "diamond"  # 마름모
    UNKNOWN = "unknown"


class Balloon(BaseModel):
    """벌룬 데이터"""
    id: str = Field(..., description="벌룬 고유 ID")
    number: str = Field(..., description="벌룬 번호 (텍스트)")
    numeric_value: Optional[int] = Field(None, description="벌룬 번호 (숫자)")

    # 형태 정보
    shape: BalloonShape = Field(BalloonShape.CIRCLE, description="벌룬 형태")

    # 매칭 정보
    matched_symbol_id: Optional[str] = Field(None, description="매칭된 심볼 ID")
    matched_symbol_class: Optional[str] = Field(None, description="매칭된 심볼 클래스")
    leader_line_endpoint: Optional[List[float]] = Field(None, description="지시선 끝점 [x, y]")

    # BOM 연결
    bom_item: Optional[Dict[str, Any]] = Field(None, description="연결된 BOM 항목")

    # 위치 정보
    center: Optional[List[float]] = Field(None, description="중심 좌표 [x, y]")
    bbox: Optional[List[float]] = Field(None, description="바운딩 박스 [x1, y1, x2, y2]")
    confidence: float = Field(0.0, description="검출 신뢰도")


class BalloonMatchingResult(BaseModel):
    """벌룬 매칭 결과"""
    session_id: str
    balloons: List[Balloon] = Field(default_factory=list)
    total_balloons: int = Field(0, description="총 벌룬 수")
    matched_count: int = Field(0, description="매칭된 벌룬 수")
    unmatched_count: int = Field(0, description="미매칭 벌룬 수")
    match_rate: float = Field(0.0, description="매칭률 (%)")
    processing_time_ms: float = Field(0.0)


# ============================================================
# 공통 응답 모델
# ============================================================

class ManufacturingFeatureResponse(BaseModel):
    """제조 기능 공통 응답"""
    success: bool = Field(True)
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
