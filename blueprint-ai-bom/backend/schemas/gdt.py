"""GD&T (Geometric Dimensioning and Tolerancing) Schemas (Phase 7)

기하공차 파싱을 위한 스키마
- Feature Control Frame (FCF): 기하공차 프레임
- Geometric Characteristics: 14가지 기하 특성
- Datum References: 데이텀 참조
- Material Condition Modifiers: 재료 조건 수정자
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .detection import BoundingBox, VerificationStatus


class GeometricCharacteristic(str, Enum):
    """기하 특성 (14종)"""
    # Form (형상 공차) - 4종
    STRAIGHTNESS = "straightness"          # 직진도 ─
    FLATNESS = "flatness"                  # 평면도 ▱
    CIRCULARITY = "circularity"            # 진원도 ○
    CYLINDRICITY = "cylindricity"          # 원통도 ⌭

    # Profile (윤곽 공차) - 2종
    PROFILE_LINE = "profile_line"          # 선의 윤곽도 ⌒
    PROFILE_SURFACE = "profile_surface"    # 면의 윤곽도 ⌓

    # Orientation (방향 공차) - 3종
    ANGULARITY = "angularity"              # 경사도 ∠
    PERPENDICULARITY = "perpendicularity"  # 직각도 ⊥
    PARALLELISM = "parallelism"            # 평행도 ∥

    # Location (위치 공차) - 3종
    POSITION = "position"                  # 위치도 ⌖
    CONCENTRICITY = "concentricity"        # 동심도 ◎
    SYMMETRY = "symmetry"                  # 대칭도 ⌯

    # Runout (흔들림 공차) - 2종
    CIRCULAR_RUNOUT = "circular_runout"    # 원주 흔들림 ↗
    TOTAL_RUNOUT = "total_runout"          # 전체 흔들림 ⇗

    # Unknown
    UNKNOWN = "unknown"


class MaterialCondition(str, Enum):
    """재료 조건 수정자"""
    MMC = "mmc"    # Maximum Material Condition (최대 실체 조건) Ⓜ
    LMC = "lmc"    # Least Material Condition (최소 실체 조건) Ⓛ
    RFS = "rfs"    # Regardless of Feature Size (크기 무관) Ⓢ
    NONE = "none"  # 수정자 없음


class GDTCategory(str, Enum):
    """GD&T 카테고리"""
    FORM = "form"              # 형상 공차
    PROFILE = "profile"        # 윤곽 공차
    ORIENTATION = "orientation" # 방향 공차
    LOCATION = "location"      # 위치 공차
    RUNOUT = "runout"          # 흔들림 공차


# 기하 특성별 카테고리 매핑
CHARACTERISTIC_CATEGORY_MAP: Dict[GeometricCharacteristic, GDTCategory] = {
    GeometricCharacteristic.STRAIGHTNESS: GDTCategory.FORM,
    GeometricCharacteristic.FLATNESS: GDTCategory.FORM,
    GeometricCharacteristic.CIRCULARITY: GDTCategory.FORM,
    GeometricCharacteristic.CYLINDRICITY: GDTCategory.FORM,
    GeometricCharacteristic.PROFILE_LINE: GDTCategory.PROFILE,
    GeometricCharacteristic.PROFILE_SURFACE: GDTCategory.PROFILE,
    GeometricCharacteristic.ANGULARITY: GDTCategory.ORIENTATION,
    GeometricCharacteristic.PERPENDICULARITY: GDTCategory.ORIENTATION,
    GeometricCharacteristic.PARALLELISM: GDTCategory.ORIENTATION,
    GeometricCharacteristic.POSITION: GDTCategory.LOCATION,
    GeometricCharacteristic.CONCENTRICITY: GDTCategory.LOCATION,
    GeometricCharacteristic.SYMMETRY: GDTCategory.LOCATION,
    GeometricCharacteristic.CIRCULAR_RUNOUT: GDTCategory.RUNOUT,
    GeometricCharacteristic.TOTAL_RUNOUT: GDTCategory.RUNOUT,
}

# 기하 특성 기호 매핑
CHARACTERISTIC_SYMBOLS: Dict[GeometricCharacteristic, str] = {
    GeometricCharacteristic.STRAIGHTNESS: "─",
    GeometricCharacteristic.FLATNESS: "▱",
    GeometricCharacteristic.CIRCULARITY: "○",
    GeometricCharacteristic.CYLINDRICITY: "⌭",
    GeometricCharacteristic.PROFILE_LINE: "⌒",
    GeometricCharacteristic.PROFILE_SURFACE: "⌓",
    GeometricCharacteristic.ANGULARITY: "∠",
    GeometricCharacteristic.PERPENDICULARITY: "⊥",
    GeometricCharacteristic.PARALLELISM: "∥",
    GeometricCharacteristic.POSITION: "⌖",
    GeometricCharacteristic.CONCENTRICITY: "◎",
    GeometricCharacteristic.SYMMETRY: "⌯",
    GeometricCharacteristic.CIRCULAR_RUNOUT: "↗",
    GeometricCharacteristic.TOTAL_RUNOUT: "⇗",
    GeometricCharacteristic.UNKNOWN: "?",
}

# 기하 특성 한글명 매핑
CHARACTERISTIC_LABELS: Dict[GeometricCharacteristic, str] = {
    GeometricCharacteristic.STRAIGHTNESS: "직진도",
    GeometricCharacteristic.FLATNESS: "평면도",
    GeometricCharacteristic.CIRCULARITY: "진원도",
    GeometricCharacteristic.CYLINDRICITY: "원통도",
    GeometricCharacteristic.PROFILE_LINE: "선의 윤곽도",
    GeometricCharacteristic.PROFILE_SURFACE: "면의 윤곽도",
    GeometricCharacteristic.ANGULARITY: "경사도",
    GeometricCharacteristic.PERPENDICULARITY: "직각도",
    GeometricCharacteristic.PARALLELISM: "평행도",
    GeometricCharacteristic.POSITION: "위치도",
    GeometricCharacteristic.CONCENTRICITY: "동심도",
    GeometricCharacteristic.SYMMETRY: "대칭도",
    GeometricCharacteristic.CIRCULAR_RUNOUT: "원주 흔들림",
    GeometricCharacteristic.TOTAL_RUNOUT: "전체 흔들림",
    GeometricCharacteristic.UNKNOWN: "미분류",
}


class DatumReference(BaseModel):
    """데이텀 참조"""
    label: str = Field(description="데이텀 레이블 (A, B, C 등)")
    material_condition: MaterialCondition = Field(
        default=MaterialCondition.NONE,
        description="재료 조건 수정자"
    )
    order: int = Field(default=1, ge=1, le=3, description="데이텀 순서 (1차, 2차, 3차)")


class ToleranceZone(BaseModel):
    """공차 영역"""
    value: float = Field(description="공차 값")
    unit: str = Field(default="mm", description="단위")
    diameter: bool = Field(default=False, description="직경 공차 여부 (⌀)")
    projected: bool = Field(default=False, description="돌출 공차대 여부 (Ⓟ)")
    material_condition: MaterialCondition = Field(
        default=MaterialCondition.NONE,
        description="재료 조건 수정자"
    )


class FeatureControlFrame(BaseModel):
    """Feature Control Frame (기하공차 프레임)"""
    id: str = Field(description="FCF ID")
    characteristic: GeometricCharacteristic = Field(description="기하 특성")
    category: Optional[GDTCategory] = Field(default=None, description="카테고리")

    # 공차 영역
    tolerance: ToleranceZone = Field(description="공차 영역")

    # 데이텀 참조 (최대 3개)
    datums: List[DatumReference] = Field(
        default=[],
        max_length=3,
        description="데이텀 참조 (1차, 2차, 3차)"
    )

    # 위치 정보
    bbox: BoundingBox = Field(description="바운딩 박스")
    bbox_normalized: Optional[List[float]] = Field(
        default=None,
        description="정규화 좌표 [x1, y1, x2, y2]"
    )

    # 연결 정보
    linked_feature_id: Optional[str] = Field(
        default=None,
        description="연결된 형상 ID (치수, 심볼 등)"
    )
    linked_dimension_id: Optional[str] = Field(
        default=None,
        description="연결된 치수 ID"
    )

    # 신뢰도 및 검증
    confidence: float = Field(ge=0, le=1, description="검출 신뢰도")
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="검증 상태"
    )

    # 원본 텍스트
    raw_text: Optional[str] = Field(default=None, description="원본 OCR 텍스트")

    # 메타데이터
    notes: Optional[str] = Field(default=None, description="비고")


class DatumFeature(BaseModel):
    """데이텀 형상"""
    id: str = Field(description="데이텀 ID")
    label: str = Field(description="데이텀 레이블 (A, B, C 등)")

    # 위치 정보
    bbox: BoundingBox = Field(description="바운딩 박스")
    bbox_normalized: Optional[List[float]] = Field(
        default=None,
        description="정규화 좌표"
    )

    # 데이텀 타입
    datum_type: str = Field(
        default="primary",
        description="데이텀 타입 (primary, secondary, tertiary)"
    )

    # 연결 정보
    linked_feature_bbox: Optional[BoundingBox] = Field(
        default=None,
        description="연결된 형상 영역"
    )

    # 신뢰도
    confidence: float = Field(ge=0, le=1, description="검출 신뢰도")
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="검증 상태"
    )


class GDTParsingConfig(BaseModel):
    """GD&T 파싱 설정"""
    # 검출 설정
    confidence_threshold: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="검출 신뢰도 임계값"
    )

    # OCR 설정
    ocr_engine: str = Field(
        default="edocr2",
        description="사용할 OCR 엔진"
    )

    # 파싱 옵션
    detect_datums: bool = Field(default=True, description="데이텀 검출")
    detect_fcf: bool = Field(default=True, description="FCF 검출")
    link_to_dimensions: bool = Field(default=True, description="치수와 연결")

    # 고급 설정
    merge_nearby_symbols: bool = Field(
        default=True,
        description="근접 심볼 병합"
    )
    merge_distance: float = Field(
        default=20.0,
        description="병합 거리 (픽셀)"
    )


class GDTParsingRequest(BaseModel):
    """GD&T 파싱 요청"""
    session_id: str
    config: Optional[GDTParsingConfig] = None
    region_ids: Optional[List[str]] = Field(
        default=None,
        description="특정 영역에서만 파싱 (비어있으면 전체)"
    )


class GDTParsingResult(BaseModel):
    """GD&T 파싱 결과"""
    session_id: str

    # FCF 결과
    fcf_list: List[FeatureControlFrame] = Field(
        default=[],
        description="검출된 FCF 목록"
    )

    # 데이텀 결과
    datums: List[DatumFeature] = Field(
        default=[],
        description="검출된 데이텀 목록"
    )

    # 이미지 정보
    image_width: int
    image_height: int

    # 통계
    total_fcf: int
    total_datums: int
    processing_time_ms: float

    # 카테고리별 통계
    fcf_by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="카테고리별 FCF 수"
    )
    fcf_by_characteristic: Dict[str, int] = Field(
        default_factory=dict,
        description="특성별 FCF 수"
    )

    created_at: datetime = Field(default_factory=datetime.now)


class FCFUpdate(BaseModel):
    """FCF 업데이트"""
    fcf_id: str
    characteristic: Optional[GeometricCharacteristic] = None
    tolerance_value: Optional[float] = None
    tolerance_unit: Optional[str] = None
    datums: Optional[List[DatumReference]] = None
    verification_status: Optional[VerificationStatus] = None
    notes: Optional[str] = None


class BulkFCFUpdate(BaseModel):
    """일괄 FCF 업데이트"""
    updates: List[FCFUpdate]


class ManualFCF(BaseModel):
    """수동 FCF 추가"""
    characteristic: GeometricCharacteristic
    tolerance_value: float
    tolerance_unit: str = "mm"
    bbox: BoundingBox
    datums: Optional[List[DatumReference]] = None
    diameter: bool = False
    material_condition: MaterialCondition = MaterialCondition.NONE


class ManualDatum(BaseModel):
    """수동 데이텀 추가"""
    label: str = Field(min_length=1, max_length=2, description="데이텀 레이블 (A, B, C 등)")
    bbox: BoundingBox
    datum_type: str = "primary"


class GDTListResponse(BaseModel):
    """GD&T 목록 응답"""
    session_id: str
    fcf_list: List[FeatureControlFrame]
    datums: List[DatumFeature]
    total_fcf: int
    total_datums: int


class GDTSummary(BaseModel):
    """GD&T 요약 정보"""
    session_id: str

    # FCF 요약
    total_fcf: int
    fcf_by_category: Dict[str, int]
    fcf_by_characteristic: Dict[str, int]

    # 데이텀 요약
    total_datums: int
    datum_labels: List[str]

    # 검증 상태
    verified_fcf: int
    pending_fcf: int

    # 품질 정보
    avg_confidence: float
    low_confidence_count: int  # 신뢰도 0.7 미만
