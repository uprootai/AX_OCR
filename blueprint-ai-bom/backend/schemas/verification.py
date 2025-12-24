"""Verification API Schemas

Active Learning 기반 검증 관련 Pydantic 모델
- 검증 액션 (승인/거부/수정)
- 검증 큐 및 통계
- 임계값 설정
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class VerificationActionType(str, Enum):
    """검증 액션 타입"""
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class Priority(str, Enum):
    """검증 우선순위"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ==================== Request Models ====================

class VerificationAction(BaseModel):
    """검증 액션 요청"""
    item_id: str = Field(..., description="검증 대상 항목 ID")
    item_type: str = Field(
        default="dimension",
        description="항목 타입 (dimension 또는 symbol)"
    )
    action: str = Field(
        ...,
        description="검증 액션 (approved, rejected, modified)"
    )
    modified_data: Optional[Dict[str, Any]] = Field(
        None,
        description="수정된 데이터 (action이 modified일 때)"
    )
    review_time_seconds: Optional[float] = Field(
        None,
        description="검증 소요 시간 (초)"
    )


class BulkApproveRequest(BaseModel):
    """일괄 승인 요청"""
    item_ids: List[str] = Field(..., description="승인할 항목 ID 목록")
    item_type: str = Field(
        default="dimension",
        description="항목 타입 (dimension 또는 symbol)"
    )


class ThresholdUpdateRequest(BaseModel):
    """임계값 업데이트 요청"""
    auto_approve_threshold: Optional[float] = Field(
        None,
        ge=0.5,
        le=1.0,
        description="자동 승인 임계값 (기본 0.9)"
    )
    critical_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=0.9,
        description="크리티컬 우선순위 임계값 (기본 0.7)"
    )


# ==================== Response Models ====================

class VerificationQueueItem(BaseModel):
    """검증 큐 항목"""
    id: str = Field(..., description="항목 ID")
    priority: str = Field(..., description="우선순위 (critical, high, medium, low)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    item_type: str = Field(..., description="항목 타입")
    data: Dict[str, Any] = Field(default_factory=dict, description="항목 데이터")


class VerificationStats(BaseModel):
    """검증 통계"""
    total: int = Field(..., ge=0, description="전체 항목 수")
    pending: int = Field(..., ge=0, description="대기 중")
    approved: int = Field(..., ge=0, description="승인됨")
    rejected: int = Field(..., ge=0, description="거부됨")
    modified: int = Field(..., ge=0, description="수정됨")
    auto_approve_candidates: int = Field(..., ge=0, description="자동 승인 후보 수")


class Thresholds(BaseModel):
    """검증 임계값"""
    auto_approve: float = Field(..., ge=0.0, le=1.0, description="자동 승인 임계값")
    critical: float = Field(..., ge=0.0, le=1.0, description="크리티컬 임계값")
    high: float = Field(..., ge=0.0, le=1.0, description="높은 우선순위 임계값")
    medium: float = Field(..., ge=0.0, le=1.0, description="중간 우선순위 임계값")


class VerificationQueueResponse(BaseModel):
    """검증 큐 응답"""
    session_id: str = Field(..., description="세션 ID")
    item_type: str = Field(..., description="항목 타입")
    queue: List[Dict[str, Any]] = Field(default_factory=list, description="검증 큐")
    stats: Dict[str, Any] = Field(default_factory=dict, description="통계")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="임계값")


class VerificationStatsResponse(BaseModel):
    """검증 통계 응답"""
    session_id: str = Field(..., description="세션 ID")
    item_type: str = Field(..., description="항목 타입")
    stats: Dict[str, Any] = Field(default_factory=dict, description="통계")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="임계값")


class AutoApproveCandidatesResponse(BaseModel):
    """자동 승인 후보 응답"""
    session_id: str = Field(..., description="세션 ID")
    item_type: str = Field(..., description="항목 타입")
    candidates: List[str] = Field(default_factory=list, description="후보 ID 목록")
    candidate_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="후보 항목 상세"
    )
    count: int = Field(..., ge=0, description="후보 수")
    threshold: float = Field(..., ge=0.0, le=1.0, description="적용된 임계값")


class VerificationResultResponse(BaseModel):
    """검증 결과 응답"""
    session_id: str = Field(..., description="세션 ID")
    item_id: str = Field(..., description="항목 ID")
    action: str = Field(..., description="수행된 액션")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="결과 메시지")


class BulkApproveResponse(BaseModel):
    """일괄 승인 응답"""
    session_id: str = Field(..., description="세션 ID")
    item_type: str = Field(..., description="항목 타입")
    requested_count: int = Field(..., ge=0, description="요청 항목 수")
    approved_count: int = Field(..., ge=0, description="승인된 항목 수")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="결과 메시지")


class VerificationLog(BaseModel):
    """검증 로그 항목"""
    item_id: str = Field(..., description="항목 ID")
    item_type: str = Field(..., description="항목 타입")
    action: str = Field(..., description="수행된 액션")
    timestamp: str = Field(..., description="타임스탬프")
    session_id: Optional[str] = Field(None, description="세션 ID")
    original_data: Optional[Dict[str, Any]] = Field(None, description="원본 데이터")
    modified_data: Optional[Dict[str, Any]] = Field(None, description="수정 데이터")


class VerificationLogsResponse(BaseModel):
    """검증 로그 목록 응답"""
    session_id: str = Field(..., description="세션 ID")
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="로그 목록")
    count: int = Field(..., ge=0, description="로그 수")


class ThresholdsResponse(BaseModel):
    """임계값 조회 응답"""
    thresholds: Dict[str, float] = Field(default_factory=dict, description="현재 임계값")


class ThresholdUpdateResponse(BaseModel):
    """임계값 업데이트 응답"""
    updated: Dict[str, float] = Field(default_factory=dict, description="업데이트된 값")
    current_thresholds: Dict[str, float] = Field(
        default_factory=dict,
        description="현재 전체 임계값"
    )


class TrainingDataResponse(BaseModel):
    """재학습 데이터 응답"""
    data: List[Dict[str, Any]] = Field(default_factory=list, description="학습 데이터")
    count: int = Field(..., ge=0, description="데이터 수")
    action_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="액션별 카운트"
    )
    filters: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="적용된 필터"
    )
