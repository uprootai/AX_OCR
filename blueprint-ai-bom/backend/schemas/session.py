"""Session Schemas"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from .classification import DrawingType  # 도면 타입은 classification.py에서 정의


class SessionStatus(str, Enum):
    """세션 상태"""
    CREATED = "created"
    UPLOADED = "uploaded"
    DETECTING = "detecting"
    DETECTED = "detected"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    GENERATING_BOM = "generating_bom"
    COMPLETED = "completed"
    ERROR = "error"


# =============================================================================
# Phase 2C: 이미지별 Human-in-the-Loop
# =============================================================================

class ImageReviewStatus(str, Enum):
    """이미지별 검토 상태"""
    PENDING = "pending"           # 검토 대기
    PROCESSED = "processed"       # 분석 완료, 검토 대기
    APPROVED = "approved"         # 승인됨
    REJECTED = "rejected"         # 거부됨
    MODIFIED = "modified"         # 수정됨 (검출 결과 편집)
    MANUAL_LABELED = "manual_labeled"  # 수동 라벨링됨


class SessionImage(BaseModel):
    """세션 내 개별 이미지"""
    model_config = ConfigDict(from_attributes=True)

    image_id: str = Field(..., description="이미지 고유 ID")
    filename: str = Field(..., description="원본 파일명")
    file_path: str = Field(..., description="저장 경로")

    # 검토 상태
    review_status: ImageReviewStatus = Field(
        default=ImageReviewStatus.PENDING,
        description="이미지 검토 상태"
    )

    # 검출 정보
    detections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="해당 이미지의 검출 결과"
    )
    detection_count: int = Field(default=0, description="검출 수")
    verified_count: int = Field(default=0, description="검증 완료 수")
    approved_count: int = Field(default=0, description="승인된 수")
    rejected_count: int = Field(default=0, description="거부된 수")

    # 이미지 메타데이터
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    thumbnail_base64: Optional[str] = Field(
        None,
        description="썸네일 이미지 (base64)"
    )

    # 검토 기록
    reviewed_at: Optional[datetime] = Field(None, description="검토 완료 시간")
    reviewed_by: Optional[str] = Field(None, description="검토자")
    review_notes: Optional[str] = Field(None, description="검토 메모")

    # 정렬용
    order_index: int = Field(default=0, description="표시 순서")


class ImageReviewUpdate(BaseModel):
    """이미지 검토 상태 업데이트"""
    review_status: ImageReviewStatus
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class BulkReviewRequest(BaseModel):
    """일괄 검토 요청"""
    image_ids: List[str] = Field(..., description="검토할 이미지 ID 목록")
    review_status: ImageReviewStatus = Field(..., description="적용할 검토 상태")
    reviewed_by: Optional[str] = Field(None, description="검토자")


class SessionImageProgress(BaseModel):
    """세션 이미지 진행률"""
    total_images: int = 0
    pending_count: int = 0
    processed_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    modified_count: int = 0
    manual_labeled_count: int = 0

    # 진행률 (0-100)
    progress_percent: float = 0.0

    # 완료 여부 (모든 이미지가 approved/modified/manual_labeled)
    all_reviewed: bool = False
    export_ready: bool = False


class SessionCreate(BaseModel):
    """세션 생성 요청"""
    filename: str
    file_path: str
    drawing_type: DrawingType = DrawingType.AUTO  # 빌더에서 설정한 도면 타입

    # Phase 2: 프로젝트/템플릿 연결
    project_id: Optional[str] = Field(None, description="프로젝트 ID")
    template_id: Optional[str] = Field(None, description="템플릿 ID")

    # Phase 2G: 워크플로우 잠금 시스템 (BlueprintFlow → 고객 배포)
    workflow_locked: bool = Field(default=False, description="워크플로우 잠금 여부")
    workflow_definition: Optional[Dict[str, Any]] = Field(
        None, description="워크플로우 정의 (nodes, edges, name)"
    )
    lock_level: str = Field(
        default="none",
        description="잠금 수준: 'full' | 'parameters' | 'none'"
    )
    allowed_parameters: List[str] = Field(
        default_factory=list,
        description="수정 가능한 파라미터 목록"
    )

    # 고객 접근
    customer_name: Optional[str] = Field(None, description="고객명")
    access_token: Optional[str] = Field(None, description="접근 토큰")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")


class SessionResponse(BaseModel):
    """세션 응답"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    filename: str
    file_path: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    detection_count: int = 0
    verified_count: int = 0
    bom_generated: bool = False
    error_message: Optional[str] = None

    # 이미지 정보
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    # 도면 분류 정보
    drawing_type: DrawingType = DrawingType.AUTO
    drawing_type_source: str = "builder"  # builder, vlm, manual
    drawing_type_confidence: Optional[float] = None  # VLM 분류 시 신뢰도

    # 활성화된 기능 목록 (2025-12-24: 기능 기반 재설계)
    features: List[str] = Field(default_factory=list)

    # Phase 2: 프로젝트/템플릿 연결
    project_id: Optional[str] = Field(None, description="프로젝트 ID")
    project_name: Optional[str] = Field(None, description="프로젝트명 (조인)")
    template_id: Optional[str] = Field(None, description="템플릿 ID")
    template_name: Optional[str] = Field(None, description="템플릿명 (조인)")
    model_type: Optional[str] = Field(None, description="YOLO 모델 타입")

    # Phase 2C: 다중 이미지 지원
    image_count: int = Field(default=0, description="이미지 수")
    images_approved: int = Field(default=0, description="승인된 이미지 수")
    images_rejected: int = Field(default=0, description="거부된 이미지 수")
    images_modified: int = Field(default=0, description="수정된 이미지 수")
    images_pending: int = Field(default=0, description="대기 중인 이미지 수")
    export_ready: bool = Field(default=False, description="Export 가능 여부")

    # Phase 2G: 워크플로우 잠금 시스템
    workflow_locked: bool = Field(default=False, description="워크플로우 잠금 여부")
    lock_level: str = Field(default="none", description="잠금 수준")
    customer_name: Optional[str] = Field(None, description="고객명")


class SessionDetail(BaseModel):
    """세션 상세 정보"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    filename: str
    file_path: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime

    # 도면 분류 정보
    drawing_type: DrawingType = DrawingType.AUTO
    drawing_type_source: str = "builder"  # builder, vlm, manual
    drawing_type_confidence: Optional[float] = None  # VLM 분류 시 신뢰도
    vlm_classification_result: Optional[str] = None  # VLM 분류 결과 (auto인 경우)

    # 활성화된 기능 목록 (2025-12-24: 기능 기반 재설계)
    features: List[str] = Field(default_factory=list)

    # Phase 2: 프로젝트/템플릿 연결
    project_id: Optional[str] = Field(None, description="프로젝트 ID")
    project_name: Optional[str] = Field(None, description="프로젝트명 (조인)")
    template_id: Optional[str] = Field(None, description="템플릿 ID")
    template_name: Optional[str] = Field(None, description="템플릿명 (조인)")
    model_type: Optional[str] = Field(None, description="YOLO 모델 타입")

    # 검출 정보
    detections: List[Dict[str, Any]] = []
    detection_count: int = 0

    # 치수 정보
    dimensions: Optional[List[Dict[str, Any]]] = Field(default=None, description="치수 추출 결과")
    dimension_count: int = Field(default=0, description="치수 수")

    # 검증 정보
    verification_status: Dict[str, str] = {}
    verified_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0

    # BOM 정보
    bom_data: Optional[Dict[str, Any]] = None
    bom_generated: bool = False
    has_custom_pricing: bool = Field(default=False, description="커스텀 단가 파일 존재 여부")

    # Phase 2C: 다중 이미지 지원
    images: List[SessionImage] = Field(default_factory=list)
    image_count: int = Field(default=0, description="이미지 수")
    images_approved: int = Field(default=0, description="승인된 이미지 수")
    images_rejected: int = Field(default=0, description="거부된 이미지 수")
    images_modified: int = Field(default=0, description="수정된 이미지 수")
    images_pending: int = Field(default=0, description="대기 중인 이미지 수")
    export_ready: bool = Field(default=False, description="Export 가능 여부")

    # 이미지 정보
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    image_base64: Optional[str] = None

    # 테이블 추출 결과 (Gateway Table Detector → BOM 세션)
    table_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="테이블 추출 결과")
    texts: Optional[List[Dict[str, Any]]] = Field(default=None, description="텍스트 추출 결과")
    text_regions: Optional[List[Dict[str, Any]]] = Field(default=None, description="비테이블 텍스트 영역 OCR 결과")

    # Phase 2G: 워크플로우 잠금 시스템
    workflow_locked: bool = Field(default=False, description="워크플로우 잠금 여부")
    workflow_definition: Optional[Dict[str, Any]] = Field(
        None, description="워크플로우 정의 (nodes, edges, name)"
    )
    lock_level: str = Field(default="none", description="잠금 수준")
    allowed_parameters: List[str] = Field(
        default_factory=list, description="수정 가능한 파라미터 목록"
    )
    customer_name: Optional[str] = Field(None, description="고객명")
    access_token: Optional[str] = Field(None, description="접근 토큰")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
