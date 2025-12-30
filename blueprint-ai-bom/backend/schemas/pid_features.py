"""P&ID 분석 기능 스키마

P&ID 도면 분석을 위한 Human-in-the-Loop 스키마 정의

기능:
1. Valve Detection: P&ID 밸브 태그 검출
2. Equipment Detection: 장비 태그 검출 및 목록화
3. Design Checklist: 설계 규칙 검증
4. Deviation Analysis: 기준 대비 편차 분석
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# =====================
# Feature Types
# =====================

class PIDFeature(str, Enum):
    """P&ID 분석 기능"""
    VALVE_DETECTION = "pid_valve_detection"       # 밸브 검출
    EQUIPMENT_DETECTION = "pid_equipment_detection"  # 장비 검출
    DESIGN_CHECKLIST = "pid_design_checklist"     # 설계 체크리스트
    DEVIATION_ANALYSIS = "pid_deviation_analysis"  # 편차 분석


class VerificationStatus(str, Enum):
    """검증 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


# =====================
# Valve Detection
# =====================

class ValveCategory(str, Enum):
    """밸브 카테고리"""
    CONTROL = "Control"           # 제어 밸브
    ISOLATION = "Isolation"       # 차단 밸브
    SAFETY = "Safety"             # 안전 밸브
    CHECK = "Check"               # 체크 밸브
    RELIEF = "Relief"             # 릴리프 밸브
    UNKNOWN = "Unknown"           # 미분류


class ValveItem(BaseModel):
    """밸브 항목"""
    id: str
    valve_id: str                               # 밸브 ID (예: XV-101)
    valve_type: str = "Unknown"                 # 밸브 타입 (예: XV, SV, CV)
    category: ValveCategory = ValveCategory.UNKNOWN
    region_name: str = ""                       # 검출된 영역
    confidence: float = 0.0
    bbox: Optional[Any] = None                  # OCR bbox
    verification_status: VerificationStatus = VerificationStatus.PENDING
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    notes: str = ""


class ValveDetectionRequest(BaseModel):
    """밸브 검출 요청"""
    rule_id: str = "valve_detection_default"
    language: str = "en"
    profile: str = "default"                    # 검출 프로필 (default, bwms, chemical 등)


class ValveDetectionResponse(BaseModel):
    """밸브 검출 응답"""
    session_id: str
    valves: List[ValveItem]
    total_count: int
    categories: Dict[str, int]
    processing_time: float
    regions_detected: int


# =====================
# Equipment Detection
# =====================

class EquipmentType(str, Enum):
    """장비 타입"""
    PUMP = "PUMP"
    VALVE = "VALVE"
    TANK = "TANK"
    HEAT_EXCHANGER = "HEAT_EXCHANGER"
    COMPRESSOR = "COMPRESSOR"
    FILTER = "FILTER"
    CONTROLLER = "CONTROLLER"
    SENSOR = "SENSOR"
    OTHER = "OTHER"


class EquipmentItem(BaseModel):
    """장비 항목"""
    id: str
    tag: str                                    # 장비 태그 (예: P-101, TK-201)
    equipment_type: EquipmentType = EquipmentType.OTHER
    description: str = ""
    vendor_supply: bool = False                 # 벤더 공급 여부
    confidence: float = 0.0
    bbox: Optional[List[float]] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    notes: str = ""


class EquipmentDetectionRequest(BaseModel):
    """장비 검출 요청"""
    profile: str = "default"                    # 검출 프로필
    language: str = "en"


class EquipmentDetectionResponse(BaseModel):
    """장비 검출 응답"""
    session_id: str
    equipment: List[EquipmentItem]
    total_count: int
    by_type: Dict[str, int]
    vendor_supply_count: int
    processing_time: float


# =====================
# Design Checklist
# =====================

class ChecklistStatus(str, Enum):
    """체크리스트 항목 상태"""
    PASS = "Pass"
    FAIL = "Fail"
    NA = "N/A"
    PENDING = "Pending"
    MANUAL = "Manual Required"


class ChecklistItem(BaseModel):
    """체크리스트 항목"""
    id: str
    item_no: int
    category: str
    description: str
    description_ko: str = ""
    auto_status: ChecklistStatus = ChecklistStatus.PENDING
    manual_status: Optional[ChecklistStatus] = None
    final_status: ChecklistStatus = ChecklistStatus.PENDING
    evidence: str = ""
    confidence: float = 0.0
    verification_status: VerificationStatus = VerificationStatus.PENDING
    reviewer_notes: str = ""
    modified_at: Optional[datetime] = None


class ChecklistRequest(BaseModel):
    """체크리스트 검사 요청"""
    enabled_rules: Optional[List[str]] = None
    rule_profile: str = "default"               # 규칙 프로필 (default, bwms, chemical 등)


class ChecklistResponse(BaseModel):
    """체크리스트 검사 응답"""
    session_id: str
    items: List[ChecklistItem]
    total_count: int
    summary: Dict[str, int]
    compliance_rate: float
    processing_time: float


# =====================
# Verification (공통)
# =====================

class PIDVerifyRequest(BaseModel):
    """P&ID 항목 검증 요청"""
    item_id: str
    item_type: str                              # valve, equipment, checklist_item
    action: str                                 # approve, reject, modify
    modified_data: Optional[Dict[str, Any]] = None
    notes: str = ""


class PIDBulkVerifyRequest(BaseModel):
    """P&ID 일괄 검증 요청"""
    item_ids: List[str]
    item_type: str
    action: str = "approve"


class PIDVerificationQueue(BaseModel):
    """P&ID 검증 큐"""
    session_id: str
    item_type: str
    queue: List[Dict[str, Any]]
    stats: Dict[str, int]
    thresholds: Dict[str, float]


# =====================
# Export (공통)
# =====================

class PIDExportRequest(BaseModel):
    """P&ID Excel 내보내기 요청"""
    export_type: str                            # valve, equipment, checklist, all
    project_name: str = "Unknown Project"
    drawing_no: str = "N/A"
    include_rejected: bool = False


class PIDExportResponse(BaseModel):
    """P&ID 내보내기 응답"""
    session_id: str
    export_type: str
    filename: str
    item_count: int
    download_url: str


# =====================
# Deviation Analysis
# =====================

class DeviationCategory(str, Enum):
    """편차 카테고리 (확장 가능한 구조)"""
    # 리비전 편차
    REVISION_ADDED = "revision_added"          # 새로 추가된 항목
    REVISION_REMOVED = "revision_removed"      # 삭제된 항목
    REVISION_MODIFIED = "revision_modified"    # 변경된 항목
    # 표준 편차
    STANDARD_VIOLATION = "standard_violation"  # 표준 위반
    STANDARD_WARNING = "standard_warning"      # 표준 경고
    # 설계 편차
    DESIGN_MISMATCH = "design_mismatch"        # 설계 불일치
    DESIGN_MISSING = "design_missing"          # 설계 누락
    # 기타
    OTHER = "other"


class DeviationSeverity(str, Enum):
    """편차 심각도"""
    CRITICAL = "critical"    # 필수 조치
    HIGH = "high"            # 중요
    MEDIUM = "medium"        # 보통
    LOW = "low"              # 낮음
    INFO = "info"            # 정보성


class DeviationSource(str, Enum):
    """편차 검출 소스 (확장 가능)"""
    REVISION_COMPARE = "revision_compare"      # 리비전 비교
    STANDARD_CHECK = "standard_check"          # 표준 검사 (ISO 10628 등)
    DESIGN_SPEC_CHECK = "design_spec_check"    # 설계 기준서 대비
    VLM_ANALYSIS = "vlm_analysis"              # VLM 기반 분석
    RULE_ENGINE = "rule_engine"                # 규칙 엔진
    MANUAL = "manual"                          # 수동 입력


class DeviationItem(BaseModel):
    """편차 항목 (범용 구조)"""
    id: str
    category: DeviationCategory
    severity: DeviationSeverity = DeviationSeverity.MEDIUM
    source: DeviationSource = DeviationSource.RULE_ENGINE

    # 편차 내용
    title: str                                  # 편차 제목
    description: str = ""                       # 상세 설명
    location: str = ""                          # 도면 내 위치 (영역명 또는 좌표)

    # 참조 정보 (선택적)
    reference_standard: Optional[str] = None    # 참조 표준 (예: ISO 10628-2)
    reference_value: Optional[str] = None       # 기준값
    actual_value: Optional[str] = None          # 실제값

    # 비교 도면 정보 (리비전 비교 시)
    baseline_info: Optional[str] = None         # 비교 기준 정보

    # 검출 메타데이터
    confidence: float = 0.0
    bbox: Optional[List[float]] = None
    evidence_image: Optional[str] = None        # base64 증거 이미지

    # Human-in-the-Loop
    verification_status: VerificationStatus = VerificationStatus.PENDING
    action_required: str = ""                   # 필요 조치
    action_taken: str = ""                      # 취해진 조치
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    notes: str = ""


class DeviationAnalysisRequest(BaseModel):
    """편차 분석 요청 (확장 가능한 구조)"""
    # 분석 타입 (하나 이상 선택)
    analysis_types: List[str] = Field(
        default=["standard_check"],
        description="분석 타입: revision_compare, standard_check, design_spec_check, vlm_analysis"
    )

    # 리비전 비교 옵션
    baseline_session_id: Optional[str] = None   # 비교 대상 세션 (리비전 비교 시)

    # 표준 검사 옵션
    standards: List[str] = Field(
        default=["ISO_10628"],
        description="적용 표준: ISO_10628, ISA_5_1, BWMS_SPEC 등"
    )

    # 설계 기준서 옵션
    design_spec_id: Optional[str] = None        # 설계 기준서 ID

    # 공통 옵션
    severity_threshold: DeviationSeverity = DeviationSeverity.LOW
    include_info: bool = True                   # INFO 수준 포함 여부
    profile: str = "default"                    # 분석 프로필


class DeviationAnalysisResponse(BaseModel):
    """편차 분석 응답"""
    session_id: str
    deviations: List[DeviationItem]
    total_count: int

    # 분석 결과 요약
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    by_source: Dict[str, int]

    # 분석 메타데이터
    analysis_types_used: List[str]
    standards_applied: List[str]
    baseline_session_id: Optional[str] = None

    processing_time: float


# =====================
# 호환성 별칭 (기존 코드 지원)
# =====================

# BWMS 특화 프로필용 별칭
ValveSignalItem = ValveItem
ValveSignalCategory = ValveCategory
ValveSignalDetectionResponse = ValveDetectionResponse
