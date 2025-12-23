"""Region Segmentation Schemas (Phase 5)

도면 영역 분할을 위한 스키마
- 도면 영역 (Main View): YOLO + OCR 적용
- 표제란 (Title Block): 메타데이터 추출
- BOM 테이블: 테이블 파싱
- 범례 (Legend): P&ID 심볼 범례
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .detection import BoundingBox, VerificationStatus


class RegionType(str, Enum):
    """도면 영역 타입 (classification.py와 동기화)"""
    TITLE_BLOCK = "title_block"       # 표제란 - 메타데이터 추출
    MAIN_VIEW = "main_view"           # 메인 도면 영역 - YOLO + OCR
    BOM_TABLE = "bom_table"           # BOM 테이블 - 테이블 파싱
    NOTES = "notes"                   # 주석/노트 영역 - OCR
    DETAIL_VIEW = "detail_view"       # 상세도 - YOLO + OCR
    SECTION_VIEW = "section_view"     # 단면도 - YOLO + OCR
    DIMENSION_AREA = "dimension_area" # 치수 영역 - OCR 집중
    LEGEND = "legend"                 # 범례 - 심볼 매칭
    REVISION_BLOCK = "revision_block" # 개정 이력 - 메타데이터
    PARTS_LIST = "parts_list"         # 부품 목록 - 테이블 파싱
    UNKNOWN = "unknown"               # 미분류 영역


class ProcessingStrategy(str, Enum):
    """영역별 처리 전략"""
    YOLO_OCR = "yolo_ocr"             # YOLO 검출 + OCR
    OCR_ONLY = "ocr_only"             # OCR만 적용
    TABLE_PARSE = "table_parse"       # 테이블 파싱
    METADATA_EXTRACT = "metadata_extract"  # 메타데이터 추출
    SYMBOL_MATCH = "symbol_match"     # 심볼 매칭
    SKIP = "skip"                     # 처리 건너뛰기


# 영역 타입별 기본 처리 전략 매핑
REGION_STRATEGY_MAP: Dict[RegionType, ProcessingStrategy] = {
    RegionType.TITLE_BLOCK: ProcessingStrategy.METADATA_EXTRACT,
    RegionType.MAIN_VIEW: ProcessingStrategy.YOLO_OCR,
    RegionType.BOM_TABLE: ProcessingStrategy.TABLE_PARSE,
    RegionType.NOTES: ProcessingStrategy.OCR_ONLY,
    RegionType.DETAIL_VIEW: ProcessingStrategy.YOLO_OCR,
    RegionType.SECTION_VIEW: ProcessingStrategy.YOLO_OCR,
    RegionType.DIMENSION_AREA: ProcessingStrategy.OCR_ONLY,
    RegionType.LEGEND: ProcessingStrategy.SYMBOL_MATCH,
    RegionType.REVISION_BLOCK: ProcessingStrategy.METADATA_EXTRACT,
    RegionType.PARTS_LIST: ProcessingStrategy.TABLE_PARSE,
    RegionType.UNKNOWN: ProcessingStrategy.SKIP,
}


class Region(BaseModel):
    """단일 영역"""
    id: str = Field(description="영역 ID")
    region_type: RegionType = Field(description="영역 타입")
    bbox: BoundingBox = Field(description="바운딩 박스 (픽셀 좌표)")
    confidence: float = Field(ge=0, le=1, description="검출 신뢰도")

    # 정규화 좌표 (0-1 범위)
    bbox_normalized: Optional[List[float]] = Field(
        default=None,
        description="[x1, y1, x2, y2] 정규화 좌표 (0-1)"
    )

    # 처리 전략
    processing_strategy: ProcessingStrategy = Field(
        default=ProcessingStrategy.SKIP,
        description="적용할 처리 전략"
    )

    # 검증 상태
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="검증 상태"
    )

    # 메타데이터
    label: Optional[str] = Field(default=None, description="사용자 레이블")
    description: Optional[str] = Field(default=None, description="영역 설명")

    # 처리 결과
    processed: bool = Field(default=False, description="처리 완료 여부")
    processing_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="영역 처리 결과 (OCR 텍스트, 테이블 데이터 등)"
    )


class RegionSegmentationConfig(BaseModel):
    """영역 분할 설정"""
    # 기본 설정
    min_region_area: float = Field(
        default=0.01,
        ge=0,
        le=1,
        description="최소 영역 면적 비율 (전체 이미지 대비)"
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="영역 검출 신뢰도 임계값"
    )

    # 영역별 처리 활성화
    detect_title_block: bool = Field(default=True, description="표제란 검출")
    detect_bom_table: bool = Field(default=True, description="BOM 테이블 검출")
    detect_legend: bool = Field(default=True, description="범례 검출")
    detect_notes: bool = Field(default=True, description="주석 영역 검출")
    detect_detail_views: bool = Field(default=True, description="상세도 검출")

    # 고급 설정
    merge_overlapping: bool = Field(
        default=True,
        description="겹치는 영역 병합"
    )
    overlap_threshold: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="병합할 겹침 비율 임계값"
    )

    # 후처리
    auto_assign_strategy: bool = Field(
        default=True,
        description="영역 타입에 따라 자동으로 처리 전략 할당"
    )


class RegionSegmentationRequest(BaseModel):
    """영역 분할 요청"""
    session_id: str
    config: Optional[RegionSegmentationConfig] = None

    # 선택적: 수동 영역 힌트
    hints: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="수동 영역 힌트 [{region_type, bbox_hint}]"
    )


class RegionSegmentationResult(BaseModel):
    """영역 분할 결과"""
    session_id: str
    regions: List[Region]

    # 메타데이터
    image_width: int
    image_height: int
    total_regions: int
    processing_time_ms: float

    # 통계
    region_stats: Dict[str, int] = Field(
        default_factory=dict,
        description="영역 타입별 개수 {region_type: count}"
    )

    created_at: datetime = Field(default_factory=datetime.now)


class RegionUpdate(BaseModel):
    """단일 영역 업데이트"""
    region_id: str
    region_type: Optional[RegionType] = None
    bbox: Optional[BoundingBox] = None
    processing_strategy: Optional[ProcessingStrategy] = None
    verification_status: Optional[VerificationStatus] = None
    label: Optional[str] = None


class BulkRegionUpdate(BaseModel):
    """일괄 영역 업데이트"""
    updates: List[RegionUpdate]


class ManualRegion(BaseModel):
    """수동 영역 추가"""
    region_type: RegionType
    bbox: BoundingBox
    label: Optional[str] = None
    processing_strategy: Optional[ProcessingStrategy] = None


class RegionProcessingResult(BaseModel):
    """영역 처리 결과"""
    region_id: str
    region_type: RegionType
    processing_strategy: ProcessingStrategy

    # 처리 결과 (전략에 따라 다름)
    success: bool
    error_message: Optional[str] = None

    # 전략별 결과
    ocr_text: Optional[str] = None
    table_data: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    symbol_matches: Optional[List[Dict[str, Any]]] = None
    detections: Optional[List[Dict[str, Any]]] = None

    processing_time_ms: float = 0


class TitleBlockData(BaseModel):
    """표제란 추출 데이터"""
    drawing_number: Optional[str] = None
    drawing_title: Optional[str] = None
    revision: Optional[str] = None
    date: Optional[str] = None
    scale: Optional[str] = None
    material: Optional[str] = None
    surface_finish: Optional[str] = None
    tolerance: Optional[str] = None
    company: Optional[str] = None
    drawn_by: Optional[str] = None
    checked_by: Optional[str] = None
    approved_by: Optional[str] = None

    # 추가 필드
    raw_text: Optional[str] = None
    custom_fields: Optional[Dict[str, str]] = None


class TableCell(BaseModel):
    """테이블 셀"""
    row: int
    col: int
    text: str
    bbox: Optional[BoundingBox] = None
    confidence: float = 1.0


class ParsedTable(BaseModel):
    """파싱된 테이블"""
    headers: List[str] = []
    rows: List[List[str]] = []
    cells: Optional[List[TableCell]] = None

    # 메타데이터
    row_count: int = 0
    col_count: int = 0
    table_type: Optional[str] = None  # "bom", "revision", "parts_list"


class RegionListResponse(BaseModel):
    """영역 목록 응답"""
    session_id: str
    regions: List[Region]
    total: int

    # 필터 정보
    filtered_by_type: Optional[RegionType] = None
    filtered_by_status: Optional[VerificationStatus] = None
