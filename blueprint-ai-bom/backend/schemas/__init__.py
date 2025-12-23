"""Blueprint AI BOM - Schemas

Pydantic 모델 정의
- Session: 세션 상태 및 정보
- Detection: 검출 결과 및 검증 상태
- Dimension: 치수 OCR 결과 및 검증 (v2 추가)
- AnalysisOptions: 분석 옵션 및 프리셋 (v2 추가)
- Line: 선 검출 및 관계 분석 (v2 추가)
- BOM: BOM 항목 및 내보내기
- Classification: VLM 기반 도면 분류 (Phase 4)
- Relation: 치수선 기반 관계 추출 (Phase 2)
"""

from .session import SessionStatus, SessionCreate, SessionResponse, SessionDetail
from .detection import (
    VerificationStatus,
    DetectionConfig,
    BoundingBox,
    Detection,
    DetectionResult,
    VerificationUpdate,
    BulkVerificationUpdate,
    ManualDetection,
)
from .dimension import (
    DimensionType,
    Dimension,
    DimensionCreate,
    DimensionUpdate,
    DimensionResult,
    DimensionListResponse,
    DimensionVerificationUpdate,
    BulkDimensionVerificationUpdate,
)
from .analysis_options import (
    AnalysisOptions,
    AnalysisOptionsUpdate,
    AnalysisResult,
    PRESETS,
    get_preset,
    apply_preset_to_options,
)
from .line import (
    LineType,
    LineStyle,
    Point,
    Line,
    Intersection,
    DimensionLineRelation,
    LineDetectionResult,
    LineDetectionConfig,
    DimensionSymbolLink,
)
from .bom import (
    ExportFormat,
    BOMItem,
    BOMSummary,
    BOMData,
    BOMExportRequest,
    BOMExportResponse,
)
from .classification import (
    DrawingType,
    RegionType,
    DetectedRegionSchema,
    ClassificationRequest,
    ClassificationResultSchema,
    PresetConfig,
    ClassificationWithPresetResponse,
)
from .relation import (
    RelationMethod,
    RelationType,
    DimensionRelationSchema,
    RelationExtractionRequest,
    RelationExtractionResult,
    RelationUpdateRequest,
    BulkRelationUpdateRequest,
    RelationStatistics,
)

__all__ = [
    # Session
    "SessionStatus",
    "SessionCreate",
    "SessionResponse",
    "SessionDetail",
    # Detection
    "VerificationStatus",
    "DetectionConfig",
    "BoundingBox",
    "Detection",
    "DetectionResult",
    "VerificationUpdate",
    "BulkVerificationUpdate",
    "ManualDetection",
    # Dimension (v2)
    "DimensionType",
    "Dimension",
    "DimensionCreate",
    "DimensionUpdate",
    "DimensionResult",
    "DimensionListResponse",
    "DimensionVerificationUpdate",
    "BulkDimensionVerificationUpdate",
    # AnalysisOptions (v2)
    "AnalysisOptions",
    "AnalysisOptionsUpdate",
    "AnalysisResult",
    "PRESETS",
    "get_preset",
    "apply_preset_to_options",
    # Line (v2)
    "LineType",
    "LineStyle",
    "Point",
    "Line",
    "Intersection",
    "DimensionLineRelation",
    "LineDetectionResult",
    "LineDetectionConfig",
    "DimensionSymbolLink",
    # BOM
    "ExportFormat",
    "BOMItem",
    "BOMSummary",
    "BOMData",
    "BOMExportRequest",
    "BOMExportResponse",
    # Classification (Phase 4)
    "DrawingType",
    "RegionType",
    "DetectedRegionSchema",
    "ClassificationRequest",
    "ClassificationResultSchema",
    "PresetConfig",
    "ClassificationWithPresetResponse",
    # Relation (Phase 2)
    "RelationMethod",
    "RelationType",
    "DimensionRelationSchema",
    "RelationExtractionRequest",
    "RelationExtractionResult",
    "RelationUpdateRequest",
    "BulkRelationUpdateRequest",
    "RelationStatistics",
]
