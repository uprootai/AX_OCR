"""TypedDict 정의 - 타입 안전성을 위한 딕셔너리 타입

Dict[str, Any] 대신 사용하여 타입 검사와 IDE 자동완성 지원
"""

from typing import TypedDict, Optional, List, Any
from typing_extensions import NotRequired


# ==================== 가격 정보 ====================

class PricingInfo(TypedDict):
    """가격 정보 타입"""
    모델명: str
    비고: str
    단가: int
    공급업체: str
    리드타임: int


# ==================== 바운딩 박스 ====================

class BBoxDict(TypedDict):
    """바운딩 박스 딕셔너리"""
    x1: float
    y1: float
    x2: float
    y2: float


# ==================== 검출 결과 ====================

class DetectionDict(TypedDict):
    """검출 결과 딕셔너리"""
    id: str
    class_name: str
    class_id: int
    confidence: float
    bbox: BBoxDict
    verification_status: str
    modified_class_name: NotRequired[Optional[str]]
    notes: NotRequired[Optional[str]]


# ==================== 치수 데이터 ====================

class DimensionDict(TypedDict):
    """치수 데이터 딕셔너리"""
    id: str
    value: str
    dimension_type: str
    confidence: float
    bbox: BBoxDict
    unit: NotRequired[Optional[str]]
    tolerance_plus: NotRequired[Optional[float]]
    tolerance_minus: NotRequired[Optional[float]]
    verification_status: NotRequired[str]
    modified_value: NotRequired[Optional[str]]


# ==================== 심볼 데이터 ====================

class SymbolDict(TypedDict):
    """심볼 데이터 딕셔너리 (검출 결과와 유사)"""
    id: str
    class_name: str
    confidence: float
    bbox: BBoxDict
    center_x: NotRequired[float]
    center_y: NotRequired[float]


# ==================== 라인 데이터 ====================

class LineDict(TypedDict):
    """라인 데이터 딕셔너리"""
    id: str
    x1: float
    y1: float
    x2: float
    y2: float
    line_type: NotRequired[str]
    confidence: NotRequired[float]


# ==================== 관계 데이터 ====================

class RelationDict(TypedDict):
    """관계 데이터 딕셔너리"""
    id: str
    dimension_id: str
    symbol_id: str
    relation_type: str
    confidence: float
    source: NotRequired[str]


# ==================== 세션 데이터 ====================

class SessionMetadata(TypedDict):
    """세션 메타데이터"""
    session_id: str
    filename: str
    file_path: str
    created_at: str
    updated_at: str
    status: str
    image_width: NotRequired[int]
    image_height: NotRequired[int]


class SessionData(TypedDict):
    """세션 전체 데이터"""
    session_id: str
    filename: str
    file_path: str
    created_at: str
    updated_at: str
    status: str
    image_width: NotRequired[int]
    image_height: NotRequired[int]
    detections: List[DetectionDict]
    dimensions: NotRequired[List[DimensionDict]]
    lines: NotRequired[List[LineDict]]
    relations: NotRequired[List[RelationDict]]
    bom_data: NotRequired[Optional[Any]]  # BOM 구조는 복잡하므로 Any 유지


# ==================== BOM 관련 ====================

class BOMItemDict(TypedDict):
    """BOM 아이템 딕셔너리"""
    item_no: int
    class_name: str
    quantity: int
    unit_price: int
    total_price: int
    model_name: NotRequired[str]
    supplier: NotRequired[str]
    lead_time: NotRequired[int]
    notes: NotRequired[str]


class BOMSummaryDict(TypedDict):
    """BOM 요약 딕셔너리"""
    total_items: int
    total_quantity: int
    total_price: int
    unique_classes: int


# ==================== API 응답 ====================

class HealthResponse(TypedDict):
    """헬스 체크 응답"""
    status: str


class ErrorResponse(TypedDict):
    """에러 응답"""
    error: str
    detail: NotRequired[str]


class SuccessResponse(TypedDict):
    """성공 응답"""
    status: str
    message: NotRequired[str]


# ==================== 통계 데이터 ====================

class StatisticsDict(TypedDict):
    """통계 딕셔너리"""
    total: int
    by_type: NotRequired[dict]
    by_confidence: NotRequired[dict]


class VerificationStatsDict(TypedDict):
    """검증 통계 딕셔너리"""
    total: int
    verified: int
    pending: int
    approved: int
    rejected: int
    modified: int
