"""치수-객체 관계 스키마 (Phase 2)

치수선 기반 관계 추출 결과를 위한 데이터 모델.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RelationMethod(str, Enum):
    """관계 추출 방법"""
    DIMENSION_LINE = "dimension_line"    # 치수선 추적 (높은 신뢰도 ~95%)
    EXTENSION_LINE = "extension_line"    # 연장선 추적 (중간 신뢰도 ~85%)
    PROXIMITY = "proximity"              # 근접성 기반 (낮은 신뢰도 ~60%)
    MANUAL = "manual"                    # 수동 지정 (100%)


class RelationType(str, Enum):
    """관계 유형"""
    DISTANCE = "distance"           # 거리 치수
    DIAMETER = "diameter"           # 직경 치수
    RADIUS = "radius"               # 반경 치수
    ANGLE = "angle"                 # 각도 치수
    TOLERANCE = "tolerance"         # 공차
    SURFACE_FINISH = "surface_finish"  # 표면 거칠기
    UNKNOWN = "unknown"


class DimensionRelationSchema(BaseModel):
    """치수-객체 관계"""
    id: str = Field(..., description="관계 ID")
    dimension_id: str = Field(..., description="치수 ID")
    target_type: str = Field(..., description="대상 유형 (symbol, edge, region, none)")
    target_id: Optional[str] = Field(None, description="대상 객체 ID")
    target_bbox: Optional[Dict[str, float]] = Field(None, description="대상 bbox")
    relation_type: str = Field(default="distance", description="관계 유형")
    method: RelationMethod = Field(..., description="추출 방법")
    confidence: float = Field(..., ge=0, le=1, description="신뢰도")
    direction: Optional[str] = Field(None, description="방향 (horizontal, vertical)")
    notes: Optional[str] = Field(None, description="비고")

    class Config:
        use_enum_values = True


class RelationExtractionRequest(BaseModel):
    """관계 추출 요청"""
    session_id: str = Field(..., description="세션 ID")
    use_lines: bool = Field(default=True, description="선 검출 결과 사용 여부")
    detect_arrows: bool = Field(default=False, description="화살표 검출 사용 (느림)")


class RelationExtractionResult(BaseModel):
    """관계 추출 결과"""
    session_id: str
    relations: List[DimensionRelationSchema]
    statistics: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float


class RelationUpdateRequest(BaseModel):
    """관계 수동 수정 요청"""
    relation_id: str
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    notes: Optional[str] = None


class BulkRelationUpdateRequest(BaseModel):
    """일괄 관계 수정 요청"""
    updates: List[RelationUpdateRequest]


class RelationStatistics(BaseModel):
    """관계 추출 통계"""
    total: int = 0
    by_method: Dict[str, int] = Field(default_factory=dict)
    by_confidence: Dict[str, int] = Field(default_factory=dict)  # high, medium, low
    linked_count: int = 0
    unlinked_count: int = 0
