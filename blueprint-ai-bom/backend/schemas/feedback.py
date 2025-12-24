"""Feedback Loop Pipeline Schemas

YOLO 재학습용 데이터셋 내보내기 관련 스키마
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """YOLO 데이터셋 내보내기 요청"""
    output_name: Optional[str] = Field(
        None,
        description="출력 디렉토리명 (None이면 타임스탬프 사용)"
    )
    include_rejected: bool = Field(
        False,
        description="거부된 항목도 포함 여부"
    )
    min_approved_rate: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="최소 승인율 (0.0-1.0)"
    )
    days_back: Optional[int] = Field(
        None,
        ge=1,
        description="최근 N일 내 세션만 포함"
    )


class ExportResponse(BaseModel):
    """YOLO 데이터셋 내보내기 응답"""
    success: bool = Field(..., description="성공 여부")
    output_path: str = Field(..., description="출력 디렉토리 경로")
    image_count: int = Field(..., ge=0, description="내보낸 이미지 수")
    label_count: int = Field(..., ge=0, description="내보낸 라벨 수")
    class_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="클래스별 라벨 수"
    )
    timestamp: str = Field(..., description="내보내기 시간 (YYYYMMDD_HHMMSS)")
    error: Optional[str] = Field(None, description="오류 메시지")


class FeedbackStatsResponse(BaseModel):
    """피드백 통계 응답"""
    total_sessions: int = Field(..., ge=0, description="총 검증 완료 세션 수")
    total_detections: int = Field(..., ge=0, description="총 검출 수")
    approved_count: int = Field(..., ge=0, description="승인된 검출 수")
    rejected_count: int = Field(..., ge=0, description="거부된 검출 수")
    modified_count: int = Field(..., ge=0, description="수정된 검출 수")
    approval_rate: float = Field(..., ge=0.0, le=1.0, description="승인율")
    rejection_rate: float = Field(..., ge=0.0, le=1.0, description="거부율")
    modification_rate: float = Field(..., ge=0.0, le=1.0, description="수정율")


class SessionStats(BaseModel):
    """세션별 검증 통계"""
    total: int = Field(..., ge=0, description="총 검출 수")
    approved: int = Field(..., ge=0, description="승인 수")
    rejected: int = Field(..., ge=0, description="거부 수")
    approval_rate: float = Field(..., ge=0.0, le=1.0, description="승인율")


class VerifiedSession(BaseModel):
    """검증 완료 세션 정보"""
    session_id: str = Field(..., description="세션 ID")
    filename: str = Field(..., description="파일명")
    stats: SessionStats = Field(..., description="검증 통계")


class VerifiedSessionsResponse(BaseModel):
    """검증 완료 세션 목록 응답"""
    sessions: List[VerifiedSession] = Field(
        default_factory=list,
        description="검증 완료 세션 목록"
    )
    count: int = Field(..., ge=0, description="세션 수")


class ExportInfo(BaseModel):
    """내보내기 정보"""
    name: str = Field(..., description="내보내기 이름")
    path: str = Field(..., description="경로")
    created_at: str = Field(..., description="생성 시간")
    image_count: int = Field(..., ge=0, description="이미지 수")
    label_count: int = Field(..., ge=0, description="라벨 수")
    class_count: int = Field(..., ge=0, description="클래스 수")


class ExportListResponse(BaseModel):
    """내보내기 목록 응답"""
    exports: List[ExportInfo] = Field(
        default_factory=list,
        description="내보내기 목록"
    )
    count: int = Field(..., ge=0, description="내보내기 수")


class FeedbackHealthResponse(BaseModel):
    """피드백 서비스 상태 응답"""
    status: str = Field(..., description="서비스 상태")
    feedback_path: str = Field(..., description="피드백 데이터 경로")
    yolo_export_path: str = Field(..., description="YOLO 내보내기 경로")
    exports_count: int = Field(..., ge=0, description="내보내기 수")
