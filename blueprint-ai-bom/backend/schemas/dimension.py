"""치수(Dimension) 관련 스키마 정의

치수 OCR 결과 및 검증을 위한 데이터 모델.
기존 Detection 스키마 패턴을 따름.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

# 기존 detection.py의 스키마 재사용
from .detection import VerificationStatus, BoundingBox


class DimensionType(str, Enum):
    """치수 유형 (gateway dimensionparser_executor.py와 동기화)"""
    LENGTH = "length"           # 길이 (100mm)
    DIAMETER = "diameter"       # 직경 (Ø50)
    RADIUS = "radius"           # 반경 (R25)
    ANGLE = "angle"             # 각도 (45°)
    TOLERANCE = "tolerance"     # 공차 (H7, ±0.1)
    SURFACE_FINISH = "surface_finish"  # 표면 거칠기 (Ra 1.6)
    THREAD = "thread"           # 나사 (M10, M10×1.5)
    CHAMFER = "chamfer"         # 챔퍼 (C2, C2×45°)
    UNKNOWN = "unknown"


class MaterialRole(str, Enum):
    """소재 견적 역할 분류

    소재 구매 시 필요한 치수 역할을 나타낸다.
    - outer_diameter: 외경 (소재 봉/링 OD 기준)
    - inner_diameter: 내경 (보어, 홀 직경)
    - length: 소재 길이 또는 폭
    - other: 가공치수, 공차, 표면거칠기 등 소재 선택과 무관
    """
    OUTER_DIAMETER = "outer_diameter"
    INNER_DIAMETER = "inner_diameter"
    LENGTH = "length"
    OTHER = "other"


class Dimension(BaseModel):
    """치수 데이터 모델

    Detection 스키마와 일관된 패턴을 따름.
    """
    id: str = Field(..., description="고유 ID (예: dim_001)")
    bbox: BoundingBox = Field(..., description="바운딩박스")
    value: str = Field(..., description="치수 값 (예: Ø50, 100mm)")
    raw_text: str = Field(..., description="OCR 원본 텍스트")
    unit: Optional[str] = Field(None, description="단위 (mm, inch 등)")
    tolerance: Optional[str] = Field(None, description="공차 (H7, ±0.1 등)")
    dimension_type: DimensionType = Field(
        default=DimensionType.UNKNOWN,
        description="치수 유형"
    )
    confidence: float = Field(..., ge=0, le=1, description="OCR 신뢰도")
    model_id: str = Field(default="edocr2", description="OCR 모델 ID")

    # 검증 관련 (Detection과 동일 패턴)
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="검증 상태"
    )
    modified_value: Optional[str] = Field(None, description="수정된 치수 값")
    modified_bbox: Optional[BoundingBox] = Field(None, description="수정된 바운딩박스")
    linked_to: Optional[str] = Field(None, description="연결된 객체 ID (심볼 등)")

    # 소재 견적용 역할 분류 (postprocess_dimensions에서 자동 설정)
    material_role: Optional[MaterialRole] = Field(
        None,
        description="소재 견적 역할: outer_diameter/inner_diameter/length/other"
    )
    ocr_corrected: bool = Field(
        False,
        description="OCR 소수점 오류 자동 교정 여부"
    )

    class Config:
        use_enum_values = True


class DimensionCreate(BaseModel):
    """치수 생성 요청 (수동 추가용)"""
    bbox: BoundingBox
    value: str
    raw_text: Optional[str] = None
    confidence: float = 1.0
    dimension_type: DimensionType = DimensionType.UNKNOWN
    unit: Optional[str] = None
    tolerance: Optional[str] = None


class DimensionUpdate(BaseModel):
    """치수 수정 요청"""
    value: Optional[str] = None
    modified_value: Optional[str] = None
    tolerance: Optional[str] = None
    unit: Optional[str] = None
    dimension_type: Optional[DimensionType] = None
    status: Optional[VerificationStatus] = None
    verification_status: Optional[VerificationStatus] = None
    linked_to: Optional[str] = None
    modified_bbox: Optional[BoundingBox] = None
    material_role: Optional[MaterialRole] = None


class DimensionResult(BaseModel):
    """치수 OCR 결과"""
    session_id: str
    dimensions: List[Dimension]
    total_count: int
    model_id: str
    processing_time_ms: float
    image_width: int
    image_height: int


class DimensionListResponse(BaseModel):
    """치수 목록 응답"""
    session_id: str
    dimensions: List[Dimension]
    total: int
    stats: dict = Field(default_factory=dict, description="상태별 카운트")


class DimensionVerificationUpdate(BaseModel):
    """치수 검증 업데이트 요청"""
    dimension_id: str
    status: VerificationStatus
    modified_value: Optional[str] = None
    modified_bbox: Optional[BoundingBox] = None


class BulkDimensionVerificationUpdate(BaseModel):
    """일괄 치수 검증 업데이트"""
    updates: List[DimensionVerificationUpdate]


class BulkDimensionImport(BaseModel):
    """eDOCr2 치수 결과 일괄 가져오기 요청

    BlueprintFlow 파이프라인에서 eDOCr2 노드의 결과를
    Blueprint AI BOM 세션에 저장하기 위한 스키마.
    """
    dimensions: List[dict] = Field(..., description="eDOCr2에서 반환된 치수 목록")
    source: str = Field(default="edocr2", description="소스 모델 ID")
    auto_approve_threshold: Optional[float] = Field(
        default=None,
        description="자동 승인 신뢰도 임계값 (예: 0.9 이상이면 자동 승인)"
    )


class BulkDimensionImportResponse(BaseModel):
    """일괄 치수 가져오기 응답"""
    session_id: str
    imported_count: int
    auto_approved_count: int = 0
    dimensions: List[Dimension]
    message: str


# ==================== Dimension Lab (OCR 엔진 비교) ====================

class DimensionCompareRequest(BaseModel):
    """OCR 엔진 비교 요청"""
    session_id: str = Field(..., description="분석 대상 세션 ID")
    ocr_engines: List[str] = Field(
        default=["paddleocr", "edocr2"],
        description="비교할 OCR 엔진 목록"
    )
    confidence_threshold: float = Field(
        default=0.5, ge=0, le=1,
        description="최소 신뢰도 임계값"
    )
    classify_roles: bool = Field(
        default=True,
        description="OD/ID/W 소재 역할 분류 수행 여부"
    )


class EngineResult(BaseModel):
    """개별 엔진 결과"""
    engine: str = Field(..., description="엔진 이름")
    dimensions: List[Dimension] = Field(default_factory=list)
    count: int = Field(0, description="검출 수")
    processing_time_ms: float = Field(0, description="처리 시간(ms)")
    error: Optional[str] = Field(None, description="에러 메시지 (실패 시)")


class DimensionCompareResponse(BaseModel):
    """OCR 엔진 비교 응답"""
    session_id: str
    image_width: int
    image_height: int
    engine_results: List[EngineResult]


# ==================== 방법론 비교 ====================

class MethodDimension(BaseModel):
    """방법론별 분류된 치수 (간소화)"""
    value: str
    confidence: float
    role: Optional[str] = None  # outer_diameter, inner_diameter, length, other, None
    bbox: Optional[dict] = None


class MethodResult(BaseModel):
    """개별 분류 방법 결과"""
    method_id: str = Field(..., description="방법 ID")
    method_name: str = Field(..., description="방법 이름")
    description: str = Field("", description="방법 설명")
    od: Optional[str] = Field(None, description="추출된 외경 값")
    id_val: Optional[str] = Field(None, description="추출된 내경 값")
    width: Optional[str] = Field(None, description="추출된 폭 값")
    od_confidence: float = Field(0)
    id_confidence: float = Field(0)
    width_confidence: float = Field(0)
    classified_dims: List[MethodDimension] = Field(default_factory=list)


class RawDimension(BaseModel):
    """오버레이용 원본 치수"""
    id: str
    value: str
    confidence: float
    dimension_type: str
    bbox: dict


class MethodCompareResponse(BaseModel):
    """방법론 비교 응답"""
    session_id: str
    image_width: int
    image_height: int
    ocr_engine: str
    ocr_time_ms: float
    total_dims: int
    raw_dimensions: List[RawDimension] = Field(default_factory=list)
    method_results: List[MethodResult]


# ==================== Ground Truth ====================

class GroundTruthDimension(BaseModel):
    """수동 Ground Truth 치수"""
    role: str = Field(..., description="od / id / w")
    value: str = Field(..., description="치수 값 (예: 150)")
    bbox: dict = Field(..., description="{x1, y1, x2, y2} 이미지 좌표")


class GroundTruthRequest(BaseModel):
    """Ground Truth 저장 요청"""
    dimensions: List[GroundTruthDimension] = Field(default_factory=list)


class GroundTruthResponse(BaseModel):
    """Ground Truth 응답"""
    session_id: str
    dimensions: List[GroundTruthDimension] = Field(default_factory=list)
    image_width: int = 0
    image_height: int = 0


# ==================== 전체 비교 (엔진×방법 매트릭스) ====================

class FullCompareRequest(BaseModel):
    """전체 엔진×방법 비교 요청"""
    session_id: str
    ocr_engines: List[str] = Field(
        default=["paddleocr", "edocr2", "easyocr", "trocr", "suryaocr", "doctr", "paddleocr_tiled"],
    )
    confidence_threshold: float = Field(default=0.5)
    methods: Optional[List[str]] = Field(
        default=None,
        description="실행할 방법 ID 목록 (None이면 전체 실행)",
    )


class CircleInfo(BaseModel):
    """검출된 원 정보"""
    cx: float
    cy: float
    radius: float
    confidence: float = 0.5


class DimLineInfo(BaseModel):
    """치수선 정보"""
    x1: float
    y1: float
    x2: float
    y2: float
    near_center: bool = False
    endpoint_type: str = "unknown"  # "center"|"circumference"|"unknown"


class RoiInfo(BaseModel):
    """OCR ROI 영역 정보"""
    x: float
    y: float
    w: float
    h: float
    ocr_text: str = ""
    symbol: str = ""


class RayCastInfo(BaseModel):
    """레이캐스트 정보"""
    origin_cx: float
    origin_cy: float
    angle_deg: float
    hit_x: float
    hit_y: float
    distance: float


class GeometryDebugInfo(BaseModel):
    """기하학 디버그 오버레이용 정보"""
    circles: List[CircleInfo] = Field(default_factory=list)
    dim_lines: List[DimLineInfo] = Field(default_factory=list)
    rois: List[RoiInfo] = Field(default_factory=list)
    rays: List[RayCastInfo] = Field(default_factory=list)
    symbols_found: List[dict] = Field(default_factory=list)


class ClassifiedDim(BaseModel):
    """분류된 치수 (오버레이용)"""
    value: str
    role: Optional[str] = None  # outer_diameter, inner_diameter, length
    confidence: float = 0
    bbox: Optional[dict] = None
    diameter_from_radius: bool = False


class CellResult(BaseModel):
    """엔진×방법 교차 셀 결과"""
    engine: str
    method_id: str
    od: Optional[str] = None
    id_val: Optional[str] = None
    width: Optional[str] = None
    od_match: Optional[bool] = None
    id_match: Optional[bool] = None
    w_match: Optional[bool] = None
    score: float = Field(0, description="정확도 (0~1)")
    classified_dims: List[ClassifiedDim] = Field(default_factory=list)
    geometry_debug: Optional[GeometryDebugInfo] = None


class FullCompareResponse(BaseModel):
    """전체 비교 응답"""
    session_id: str
    image_width: int
    image_height: int
    ground_truth: List[GroundTruthDimension] = Field(default_factory=list)
    engine_times: dict = Field(default_factory=dict, description="엔진별 처리시간(ms)")
    matrix: List[CellResult] = Field(default_factory=list)
    total_engines: int = 0
    total_methods: int = 0
