"""VLM 분류 스키마 (Phase 4)"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class DrawingType(str, Enum):
    """
    도면 타입

    2025-12-22: 빌더 drawing_type과 동기화
    - dimension: 치수 도면 (shaft, 플랜지) - YOLO 불필요
    - electrical_panel: 전기 제어판 (MCP Panel) - YOLO 14클래스
    - pid: P&ID 배관계장도 - YOLO-PID 60클래스
    - assembly: 조립도 - YOLO + eDOCr2
    - dimension_bom: 치수 + BOM - eDOCr2 + SkinModel + AI BOM
    """
    AUTO = "auto"  # VLM 자동 분류 (빌더에서 설정)

    # ===== 주요 도면 타입 (빌더 동기화) =====
    DIMENSION = "dimension"  # 치수 도면 (shaft, 플랜지) - OCR만 사용
    ELECTRICAL_PANEL = "electrical_panel"  # 전기 제어판 (MCP Panel) - YOLO 14클래스
    PID = "pid"  # P&ID (배관계장도) - YOLO-PID 60클래스
    ASSEMBLY = "assembly"  # 조립도 - YOLO + eDOCr2
    DIMENSION_BOM = "dimension_bom"  # 치수 + BOM - OCR + 수동 라벨링

    # ===== 레거시 타입 (하위 호환) =====
    MECHANICAL = "mechanical"  # (deprecated) → DIMENSION 또는 ELECTRICAL_PANEL 사용
    MECHANICAL_PART = "mechanical_part"  # (deprecated) → DIMENSION 사용
    ELECTRICAL = "electrical"  # (deprecated) → ELECTRICAL_PANEL 사용
    ELECTRICAL_CIRCUIT = "electrical_circuit"  # 전기 회로도 (지원 제한적)

    # ===== 기타 =====
    ARCHITECTURAL = "architectural"  # 건축 도면 (지원 제한적)
    UNKNOWN = "unknown"  # VLM 분류 실패 시


class RegionType(str, Enum):
    """도면 영역 타입"""
    TITLE_BLOCK = "title_block"
    MAIN_VIEW = "main_view"
    BOM_TABLE = "bom_table"
    NOTES = "notes"
    DETAIL_VIEW = "detail_view"
    SECTION_VIEW = "section_view"
    DIMENSION_AREA = "dimension_area"


class DetectedRegionSchema(BaseModel):
    """검출된 영역 스키마"""
    region_type: RegionType
    bbox: List[float] = Field(description="[x1, y1, x2, y2] normalized 좌표")
    confidence: float = Field(ge=0, le=1)
    description: Optional[str] = None


class ClassificationRequest(BaseModel):
    """분류 요청"""
    session_id: Optional[str] = None
    image_base64: Optional[str] = Field(None, description="Base64 인코딩된 이미지")
    image_path: Optional[str] = Field(None, description="이미지 파일 경로")
    provider: Optional[str] = Field("local", description="VLM 프로바이더 (local, openai, anthropic)")


class ClassificationResultSchema(BaseModel):
    """분류 결과 스키마"""
    drawing_type: DrawingType
    confidence: float = Field(ge=0, le=1)
    suggested_preset: str
    regions: List[DetectedRegionSchema] = []
    analysis_notes: str = ""
    provider: str = "unknown"


class PresetConfig(BaseModel):
    """프리셋 설정"""
    name: str
    description: str
    nodes: List[str]
    yolo_confidence: Optional[float] = None
    ocr_engine: Optional[str] = None
    enable_tolerance_analysis: Optional[bool] = None
    enable_connectivity: Optional[bool] = None
    enable_bom: Optional[bool] = None
    enable_part_matching: Optional[bool] = None
    enable_circuit_analysis: Optional[bool] = None
    enable_floor_plan_analysis: Optional[bool] = None


class ClassificationWithPresetResponse(BaseModel):
    """분류 및 프리셋 응답"""
    classification: ClassificationResultSchema
    preset: PresetConfig
    session_id: Optional[str] = None
