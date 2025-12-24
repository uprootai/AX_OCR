"""Feedback Loop Pipeline Router

검증 데이터 수집 및 YOLO 데이터셋 내보내기 API
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from services.session_service import SessionService
from services.feedback_pipeline import FeedbackPipelineService
from schemas import (
    ExportRequest,
    ExportResponse,
    FeedbackStatsResponse,
    VerifiedSession,
    VerifiedSessionsResponse,
    SessionStats,
    ExportInfo,
    ExportListResponse,
    FeedbackHealthResponse,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])

# 서비스 인스턴스 (API 서버에서 주입)
_session_service: Optional[SessionService] = None
_feedback_pipeline: Optional[FeedbackPipelineService] = None


def set_feedback_services(session_service: SessionService):
    """서비스 인스턴스 주입"""
    global _session_service, _feedback_pipeline
    _session_service = session_service
    _feedback_pipeline = FeedbackPipelineService(session_service)


def get_pipeline() -> FeedbackPipelineService:
    """FeedbackPipelineService 반환"""
    if _feedback_pipeline is None:
        raise HTTPException(status_code=500, detail="Feedback service not initialized")
    return _feedback_pipeline


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    days_back: Optional[int] = Query(None, description="최근 N일 내 데이터만 조회")
):
    """
    피드백 통계 조회

    검증된 세션들의 승인/거부/수정 통계
    """
    pipeline = get_pipeline()
    stats = pipeline.get_feedback_stats(days_back=days_back)
    return FeedbackStatsResponse(**stats)


@router.get("/sessions", response_model=VerifiedSessionsResponse)
async def list_verified_sessions(
    min_approved_rate: float = Query(0.5, description="최소 승인율"),
    days_back: Optional[int] = Query(None, description="최근 N일 내 세션만")
):
    """
    검증 완료 세션 목록

    피드백 수집 가능한 세션들을 조회
    """
    pipeline = get_pipeline()
    sessions = pipeline.collect_verified_sessions(
        min_approved_rate=min_approved_rate,
        days_back=days_back
    )

    verified_sessions = [
        VerifiedSession(
            session_id=s["session_id"],
            filename=s["filename"],
            stats=SessionStats(**s["stats"])
        )
        for s in sessions
    ]

    return VerifiedSessionsResponse(
        sessions=verified_sessions,
        count=len(verified_sessions)
    )


@router.post("/export/yolo", response_model=ExportResponse)
async def export_yolo_dataset(request: ExportRequest):
    """
    YOLO 형식 데이터셋 내보내기

    검증된 데이터를 YOLO 재학습용 형식으로 내보내기
    """
    pipeline = get_pipeline()

    # 세션 수집
    sessions = pipeline.collect_verified_sessions(
        min_approved_rate=request.min_approved_rate,
        days_back=request.days_back
    )

    if not sessions:
        raise HTTPException(
            status_code=404,
            detail="No verified sessions found matching criteria"
        )

    # 내보내기
    result = pipeline.export_yolo_dataset(
        sessions=sessions,
        output_name=request.output_name,
        include_rejected=request.include_rejected
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return ExportResponse(
        success=result.success,
        output_path=result.output_path,
        image_count=result.image_count,
        label_count=result.label_count,
        class_distribution=result.class_distribution,
        timestamp=result.timestamp,
        error=result.error
    )


@router.get("/exports", response_model=ExportListResponse)
async def list_exports():
    """
    내보내기 목록 조회

    이전에 생성된 YOLO 데이터셋 목록
    """
    pipeline = get_pipeline()
    exports = pipeline.list_exports()

    export_infos = [
        ExportInfo(
            name=e["name"],
            path=e["path"],
            created_at=e.get("created_at", ""),
            image_count=e.get("image_count", 0),
            label_count=e.get("label_count", 0),
            class_count=e.get("class_count", 0)
        )
        for e in exports
    ]

    return ExportListResponse(
        exports=export_infos,
        count=len(export_infos)
    )


@router.get("/health", response_model=FeedbackHealthResponse)
async def feedback_health():
    """피드백 서비스 상태"""
    pipeline = get_pipeline()

    return FeedbackHealthResponse(
        status="healthy",
        feedback_path=str(pipeline.feedback_path),
        yolo_export_path=str(pipeline.yolo_export_path),
        exports_count=len(pipeline.list_exports())
    )
