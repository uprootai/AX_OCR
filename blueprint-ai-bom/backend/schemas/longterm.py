"""
Long-term Roadmap Feature Schemas
장기 로드맵 기능 스키마 정의 (2025-12-24)

- 도면 영역 세분화 (drawing_region_segmentation)
- 주석/노트 추출 (notes_extraction)
- 리비전 비교 (revision_comparison)
- VLM 자동 분류 (vlm_auto_classification)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# 도면 영역 세분화 (Drawing Region Segmentation)
# ============================================================

class ViewType(str, Enum):
    """도면 뷰 타입"""
    FRONT = "front"  # 정면도
    SIDE = "side"  # 측면도
    TOP = "top"  # 평면도
    BOTTOM = "bottom"  # 저면도
    SECTION = "section"  # 단면도
    DETAIL = "detail"  # 상세도
    ISOMETRIC = "isometric"  # 등각투영도
    AUXILIARY = "auxiliary"  # 보조 투영도
    TITLE_BLOCK = "title_block"  # 표제란
    PARTS_LIST = "parts_list"  # 부품 목록
    NOTES = "notes"  # 노트 영역
    REVISION_BLOCK = "revision_block"  # 리비전 블록
    UNKNOWN = "unknown"


class DrawingRegion(BaseModel):
    """도면 영역 데이터"""
    id: str = Field(..., description="영역 고유 ID")
    view_type: ViewType = Field(ViewType.UNKNOWN, description="뷰 타입")
    label: Optional[str] = Field(None, description="영역 라벨 (예: A-A 단면)")

    # 위치 정보
    bbox: List[float] = Field(default_factory=list, description="바운딩 박스 [x1, y1, x2, y2]")
    mask: Optional[List[List[float]]] = Field(None, description="세그멘테이션 마스크 폴리곤")
    area: Optional[float] = Field(None, description="영역 면적 (픽셀)")

    # 스케일 정보
    scale: Optional[str] = Field(None, description="스케일 (예: 1:2, 2:1)")

    # 메타데이터
    confidence: float = Field(0.0, description="검출 신뢰도")
    contains_dimensions: bool = Field(False, description="치수 포함 여부")
    contains_annotations: bool = Field(False, description="주석 포함 여부")

    # 관련 영역
    parent_region_id: Optional[str] = Field(None, description="상위 영역 ID")
    related_region_ids: List[str] = Field(default_factory=list, description="관련 영역 ID (예: 상세도-원본)")


class RegionSegmentationConfig(BaseModel):
    """영역 세분화 설정"""
    min_region_area: int = Field(1000, description="최소 영역 면적 (픽셀)")
    merge_threshold: float = Field(0.5, description="영역 병합 임계값")
    detect_title_block: bool = Field(True, description="표제란 검출 여부")
    detect_notes: bool = Field(True, description="노트 영역 검출 여부")


class DrawingRegionSegmentationResult(BaseModel):
    """도면 영역 세분화 결과"""
    session_id: str
    regions: List[DrawingRegion] = Field(default_factory=list)
    total_regions: int = Field(0, description="총 영역 수")
    by_view_type: Dict[str, int] = Field(default_factory=dict, description="뷰 타입별 개수")
    has_title_block: bool = Field(False, description="표제란 존재 여부")
    has_parts_list: bool = Field(False, description="부품 목록 존재 여부")
    processing_time_ms: float = Field(0.0)


# ============================================================
# 주석/노트 추출 (Notes Extraction)
# ============================================================

class NoteCategory(str, Enum):
    """노트 카테고리"""
    MATERIAL = "material"  # 재료 사양
    HEAT_TREATMENT = "heat_treatment"  # 열처리
    SURFACE_FINISH = "surface_finish"  # 표면 처리
    TOLERANCE = "tolerance"  # 일반 공차
    ASSEMBLY = "assembly"  # 조립 지시
    INSPECTION = "inspection"  # 검사 요구사항
    WELDING = "welding"  # 용접 지시
    COATING = "coating"  # 도금/도장
    THREAD = "thread"  # 나사 가공
    REFERENCE = "reference"  # 참조 문서
    GENERAL = "general"  # 기타 일반 노트
    UNKNOWN = "unknown"


class ExtractedNote(BaseModel):
    """추출된 노트 데이터"""
    id: str = Field(..., description="노트 고유 ID")
    category: NoteCategory = Field(NoteCategory.UNKNOWN, description="노트 카테고리")

    # 텍스트 내용
    text: str = Field("", description="노트 전체 텍스트")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="구조화된 데이터 (키-값)")

    # 위치 정보
    bbox: Optional[List[float]] = Field(None, description="바운딩 박스 [x1, y1, x2, y2]")
    region_id: Optional[str] = Field(None, description="소속 영역 ID")

    # 참조 정보
    references: List[str] = Field(default_factory=list, description="참조 문서/규격 목록")
    related_item_ids: List[str] = Field(default_factory=list, description="관련 항목 ID (심볼, 치수 등)")

    # 메타데이터
    confidence: float = Field(0.0, description="추출 신뢰도")
    is_numbered: bool = Field(False, description="번호가 있는 노트 (예: 1. 2. 3.)")
    note_number: Optional[int] = Field(None, description="노트 번호")


class NotesExtractionConfig(BaseModel):
    """노트 추출 설정"""
    extract_materials: bool = Field(True, description="재료 사양 추출")
    extract_tolerances: bool = Field(True, description="공차 정보 추출")
    extract_references: bool = Field(True, description="참조 문서 추출")
    use_llm_classification: bool = Field(False, description="LLM 분류 사용 여부")
    llm_provider: Optional[str] = Field(None, description="LLM 제공자 (openai, anthropic)")


class NotesExtractionResult(BaseModel):
    """노트 추출 결과"""
    session_id: str
    notes: List[ExtractedNote] = Field(default_factory=list)
    total_notes: int = Field(0, description="총 노트 수")
    by_category: Dict[str, int] = Field(default_factory=dict, description="카테고리별 개수")

    # 주요 추출 정보 요약
    materials: List[str] = Field(default_factory=list, description="추출된 재료 목록")
    standards: List[str] = Field(default_factory=list, description="참조된 표준/규격 목록")
    tolerances: Optional[Dict[str, str]] = Field(None, description="일반 공차 정보")

    processing_time_ms: float = Field(0.0)


# ============================================================
# 리비전 비교 (Revision Comparison)
# ============================================================

class ChangeType(str, Enum):
    """변경 타입"""
    ADDED = "added"  # 추가됨
    REMOVED = "removed"  # 삭제됨
    MODIFIED = "modified"  # 수정됨
    MOVED = "moved"  # 위치 이동
    SCALED = "scaled"  # 크기 변경
    UNCHANGED = "unchanged"  # 변경 없음


class ChangeCategory(str, Enum):
    """변경 카테고리"""
    GEOMETRY = "geometry"  # 형상 변경
    DIMENSION = "dimension"  # 치수 변경
    TOLERANCE = "tolerance"  # 공차 변경
    NOTE = "note"  # 노트 변경
    SYMBOL = "symbol"  # 심볼 변경
    ANNOTATION = "annotation"  # 주석 변경
    TITLE_BLOCK = "title_block"  # 표제란 변경
    OTHER = "other"


class RevisionChange(BaseModel):
    """리비전 변경 항목"""
    id: str = Field(..., description="변경 항목 ID")
    change_type: ChangeType = Field(ChangeType.MODIFIED, description="변경 타입")
    category: ChangeCategory = Field(ChangeCategory.OTHER, description="변경 카테고리")

    # 변경 내용
    description: str = Field("", description="변경 설명")
    old_value: Optional[str] = Field(None, description="이전 값")
    new_value: Optional[str] = Field(None, description="새 값")

    # 위치 정보
    bbox_old: Optional[List[float]] = Field(None, description="이전 위치 [x1, y1, x2, y2]")
    bbox_new: Optional[List[float]] = Field(None, description="새 위치 [x1, y1, x2, y2]")

    # 이미지 좌표 (오버레이용)
    highlight_points: List[List[float]] = Field(default_factory=list, description="하이라이트 포인트")

    # 메타데이터
    confidence: float = Field(0.0, description="감지 신뢰도")
    severity: str = Field("info", description="중요도 (critical, warning, info)")


class RevisionComparisonConfig(BaseModel):
    """리비전 비교 설정"""
    alignment_method: str = Field("sift", description="이미지 정합 방법 (sift, orb, feature)")
    pixel_threshold: int = Field(10, description="픽셀 차이 임계값")
    compare_dimensions: bool = Field(True, description="치수 값 비교")
    compare_notes: bool = Field(True, description="노트 비교")
    ignore_minor_changes: bool = Field(True, description="미세 변경 무시")


class RevisionComparisonRequest(BaseModel):
    """리비전 비교 요청"""
    session_id_old: str = Field(..., description="이전 리비전 세션 ID")
    session_id_new: str = Field(..., description="새 리비전 세션 ID")
    config: Optional[RevisionComparisonConfig] = Field(None, description="비교 설정")


class RevisionComparisonResult(BaseModel):
    """리비전 비교 결과"""
    session_id_old: str
    session_id_new: str

    # 변경 사항
    changes: List[RevisionChange] = Field(default_factory=list)
    total_changes: int = Field(0, description="총 변경 수")
    by_type: Dict[str, int] = Field(default_factory=dict, description="변경 타입별 개수")
    by_category: Dict[str, int] = Field(default_factory=dict, description="카테고리별 개수")

    # 요약 통계
    added_count: int = Field(0, description="추가된 항목 수")
    removed_count: int = Field(0, description="삭제된 항목 수")
    modified_count: int = Field(0, description="수정된 항목 수")

    # 비교 이미지 (Base64 또는 URL)
    diff_image_url: Optional[str] = Field(None, description="차이 이미지 URL")
    overlay_image_url: Optional[str] = Field(None, description="오버레이 이미지 URL")

    # 메타데이터
    alignment_score: float = Field(0.0, description="이미지 정합 점수")
    processing_time_ms: float = Field(0.0)


# ============================================================
# VLM 자동 분류 (VLM Auto Classification)
# ============================================================

class DrawingClassification(str, Enum):
    """도면 분류"""
    MECHANICAL_PART = "mechanical_part"  # 기계 부품도
    ASSEMBLY = "assembly"  # 조립도
    PID = "pid"  # P&ID 배관계장도
    ELECTRICAL = "electrical"  # 전기 회로도
    ARCHITECTURAL = "architectural"  # 건축 도면
    CIVIL = "civil"  # 토목 도면
    PCB = "pcb"  # PCB 회로도
    SCHEMATIC = "schematic"  # 계통도
    OTHER = "other"


class IndustryDomain(str, Enum):
    """산업 분야"""
    AUTOMOTIVE = "automotive"  # 자동차
    AEROSPACE = "aerospace"  # 항공우주
    SHIPBUILDING = "shipbuilding"  # 조선
    PLANT = "plant"  # 플랜트
    SEMICONDUCTOR = "semiconductor"  # 반도체
    MACHINERY = "machinery"  # 기계
    ELECTRONICS = "electronics"  # 전자
    CONSTRUCTION = "construction"  # 건설
    GENERAL = "general"


class ComplexityLevel(str, Enum):
    """도면 복잡도"""
    SIMPLE = "simple"  # 단순 (부품 1-5개)
    MODERATE = "moderate"  # 보통 (부품 5-20개)
    COMPLEX = "complex"  # 복잡 (부품 20-50개)
    VERY_COMPLEX = "very_complex"  # 매우 복잡 (부품 50개 이상)


class VLMClassificationResult(BaseModel):
    """VLM 분류 결과"""
    session_id: str

    # 도면 분류
    drawing_type: DrawingClassification = Field(DrawingClassification.OTHER, description="도면 타입")
    drawing_type_confidence: float = Field(0.0, description="분류 신뢰도")

    # 산업 분야
    industry_domain: IndustryDomain = Field(IndustryDomain.GENERAL, description="산업 분야")
    industry_confidence: float = Field(0.0, description="산업 분야 신뢰도")

    # 복잡도
    complexity: ComplexityLevel = Field(ComplexityLevel.MODERATE, description="복잡도")
    estimated_part_count: Optional[int] = Field(None, description="예상 부품 수")

    # 도면 특성
    has_dimensions: bool = Field(False, description="치수 포함")
    has_tolerances: bool = Field(False, description="공차 포함")
    has_surface_finish: bool = Field(False, description="표면 거칠기 포함")
    has_welding_symbols: bool = Field(False, description="용접 기호 포함")
    has_gdt: bool = Field(False, description="GD&T 포함")
    has_bom: bool = Field(False, description="BOM/부품 목록 포함")
    has_notes: bool = Field(False, description="노트 포함")
    has_title_block: bool = Field(False, description="표제란 포함")

    # 추천 기능
    recommended_features: List[str] = Field(default_factory=list, description="추천 기능 목록")

    # VLM 분석 텍스트
    analysis_summary: Optional[str] = Field(None, description="VLM 분석 요약")
    raw_response: Optional[str] = Field(None, description="VLM 원본 응답")

    # 메타데이터
    vlm_provider: str = Field("local", description="VLM 제공자 (local, openai, anthropic, google)")
    vlm_model: Optional[str] = Field(None, description="VLM 모델명")
    processing_time_ms: float = Field(0.0)


class VLMClassificationConfig(BaseModel):
    """VLM 분류 설정"""
    provider: str = Field("local", description="VLM 제공자 (local, openai, anthropic, google)")
    model: Optional[str] = Field(None, description="특정 모델 지정")
    recommend_features: bool = Field(True, description="기능 추천 포함")
    detailed_analysis: bool = Field(False, description="상세 분석 포함")
    language: str = Field("ko", description="응답 언어")


# ============================================================
# 공통 업데이트/응답 모델
# ============================================================

class DrawingRegionUpdate(BaseModel):
    """도면 영역 업데이트"""
    view_type: Optional[ViewType] = None
    label: Optional[str] = None
    scale: Optional[str] = None
    bbox: Optional[List[float]] = None


class ExtractedNoteUpdate(BaseModel):
    """노트 업데이트"""
    category: Optional[NoteCategory] = None
    text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None


class LongtermFeatureResponse(BaseModel):
    """장기 기능 공통 응답"""
    success: bool = Field(True)
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
