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
    """치수 유형"""
    LENGTH = "length"           # 길이 (100mm)
    DIAMETER = "diameter"       # 직경 (Ø50)
    RADIUS = "radius"           # 반경 (R25)
    ANGLE = "angle"             # 각도 (45°)
    TOLERANCE = "tolerance"     # 공차 (H7, ±0.1)
    SURFACE_FINISH = "surface_finish"  # 표면 거칠기 (Ra 1.6)
    UNKNOWN = "unknown"


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
    tolerance: Optional[str] = None
    unit: Optional[str] = None
    dimension_type: Optional[DimensionType] = None
    status: Optional[VerificationStatus] = None
    linked_to: Optional[str] = None
    modified_bbox: Optional[BoundingBox] = None


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
