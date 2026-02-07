"""Batch Analysis Router - 프로젝트 단위 일괄 분석

배치 분석 실행/진행률 조회:
- POST /analysis/batch/{project_id} → 백그라운드 일괄 분석 시작
- GET  /analysis/batch/{project_id}/status → 진행률 조회
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis/batch", tags=["batch-analysis"])


# ==================== 진행률 추적 ====================

class BatchProgress(BaseModel):
    """배치 분석 진행률"""
    project_id: str
    status: str = "idle"  # idle, running, completed, error
    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    current_session: Optional[str] = None
    current_drawing: Optional[str] = None
    errors: list = Field(default_factory=list)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    @property
    def progress_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.completed + self.failed + self.skipped) / self.total * 100, 1)


# 프로젝트별 진행률 (in-memory)
_batch_progress: Dict[str, BatchProgress] = {}


class BatchRunRequest(BaseModel):
    """배치 분석 요청"""
    root_drawing_number: Optional[str] = Field(
        None, description="특정 어셈블리만 분석 (None이면 전체)"
    )
    force_rerun: bool = Field(
        False, description="이미 분석된 세션도 재실행"
    )


class BatchRunResponse(BaseModel):
    """배치 분석 응답"""
    project_id: str
    status: str
    total: int
    message: str


# ==================== 엔드포인트 ====================

@router.post("/{project_id}", response_model=BatchRunResponse)
async def start_batch_analysis(project_id: str, request: BatchRunRequest = None):
    """프로젝트 전체 세션 일괄 분석 시작 (백그라운드)"""
    if request is None:
        request = BatchRunRequest()

    # 이미 실행 중이면 거부
    existing = _batch_progress.get(project_id)
    if existing and existing.status == "running":
        raise HTTPException(
            status_code=409,
            detail=f"이미 분석 실행 중입니다 ({existing.completed}/{existing.total})"
        )

    # 프로젝트 + BOM 데이터 로드
    from services.project_service import get_project_service
    from services.bom_pdf_parser import BOMPDFParser

    project_service = get_project_service(Path("/app/data"))
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    project_dir = project_service.projects_dir / project_id
    bom_parser = BOMPDFParser()
    bom_data = bom_parser.load_bom_items(project_dir)
    if not bom_data:
        raise HTTPException(status_code=404, detail="BOM 데이터가 없습니다")

    # 분석 대상 세션 수집
    items = bom_data["items"]

    # 어셈블리 스코프 필터
    if request.root_drawing_number:
        from routers.project_router import _get_subtree_items
        items = _get_subtree_items(items, request.root_drawing_number)
        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"어셈블리를 찾을 수 없습니다: {request.root_drawing_number}"
            )

    # session_id가 있는 항목만 (중복 제거)
    session_ids = {}
    for item in items:
        sid = item.get("session_id")
        if sid and sid not in session_ids:
            session_ids[sid] = item.get("drawing_number", "")

    if not session_ids:
        raise HTTPException(status_code=400, detail="분석할 세션이 없습니다")

    # 진행률 초기화
    progress = BatchProgress(
        project_id=project_id,
        status="running",
        total=len(session_ids),
        started_at=time.time(),
    )
    _batch_progress[project_id] = progress

    # 백그라운드 실행
    asyncio.create_task(
        _run_batch(project_id, session_ids, request.force_rerun)
    )

    return BatchRunResponse(
        project_id=project_id,
        status="running",
        total=len(session_ids),
        message=f"{len(session_ids)}개 세션 분석 시작",
    )


@router.get("/{project_id}/status", response_model=BatchProgress)
async def get_batch_status(project_id: str):
    """배치 분석 진행률 조회"""
    progress = _batch_progress.get(project_id)
    if not progress:
        return BatchProgress(project_id=project_id, status="idle")
    return progress


@router.delete("/{project_id}")
async def cancel_batch(project_id: str):
    """배치 분석 취소"""
    progress = _batch_progress.get(project_id)
    if not progress or progress.status != "running":
        raise HTTPException(status_code=400, detail="실행 중인 분석이 없습니다")

    progress.status = "cancelled"
    return {"message": "취소 요청됨", "completed": progress.completed, "total": progress.total}


# ==================== 백그라운드 실행 ====================

async def _run_batch(
    project_id: str,
    session_ids: Dict[str, str],
    force_rerun: bool,
):
    """세션을 순차적으로 분석 (비동기 백그라운드)"""
    from .core_router import get_session_service

    progress = _batch_progress[project_id]
    session_service = get_session_service()

    for session_id, drawing_number in session_ids.items():
        # 취소 확인
        if progress.status == "cancelled":
            break

        progress.current_session = session_id
        progress.current_drawing = drawing_number

        # 이미 분석된 세션 스킵
        session = session_service.get_session(session_id)
        if not session:
            progress.failed += 1
            progress.errors.append(f"{drawing_number}: 세션 없음")
            continue

        status = session.get("status", "")
        if status in ("verified", "completed") and not force_rerun:
            progress.skipped += 1
            continue

        # 이미지 파일 확인
        file_path = session.get("file_path", "")
        if not file_path or not Path(file_path).exists():
            progress.failed += 1
            progress.errors.append(f"{drawing_number}: 이미지 없음")
            continue

        # 분석 실행 (내부 API 직접 호출)
        try:
            from .core_router import run_analysis
            await run_analysis(session_id)
            progress.completed += 1
            logger.info(
                f"[배치] {drawing_number} 완료 "
                f"({progress.completed + progress.skipped + progress.failed}/{progress.total})"
            )
        except Exception as e:
            progress.failed += 1
            progress.errors.append(f"{drawing_number}: {str(e)[:100]}")
            logger.error(f"[배치] {drawing_number} 실패: {e}")

        # 각 세션 사이 짧은 대기 (서버 안정성)
        await asyncio.sleep(0.5)

    progress.status = "completed" if progress.status != "cancelled" else "cancelled"
    progress.current_session = None
    progress.current_drawing = None
    progress.finished_at = time.time()

    elapsed = progress.finished_at - (progress.started_at or progress.finished_at)
    logger.info(
        f"[배치] 프로젝트 {project_id} 완료: "
        f"{progress.completed}성공, {progress.skipped}스킵, {progress.failed}실패 "
        f"({elapsed:.0f}초)"
    )
