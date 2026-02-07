"""Workflow Session Router - 워크플로우 잠금 세션 API 엔드포인트

Phase 2G: BlueprintFlow -> 고객 배포를 위한 워크플로우 세션 관리
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from schemas.session import SessionStatus
from schemas.workflow_session import (
    WorkflowSessionCreate,
    WorkflowSessionResponse,
    WorkflowSessionDetail,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


# 의존성 주입을 위한 전역 서비스 (api_server.py에서 설정)
_session_service = None


def set_session_service(service):
    """서비스 인스턴스 설정"""
    global _session_service
    _session_service = service


def get_session_service():
    """세션 서비스 의존성"""
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


@router.post("/from-workflow", response_model=WorkflowSessionResponse)
async def create_session_from_workflow(
    request: WorkflowSessionCreate,
):
    """BlueprintFlow 워크플로우로부터 잠긴 세션 생성

    Args:
        request: 워크플로우 세션 생성 요청

    Returns:
        WorkflowSessionResponse: 생성된 세션 정보 (공유 URL, 접근 토큰 포함)
    """
    service = get_session_service()

    session = service.create_locked_session(
        workflow_name=request.name,
        workflow_definition={
            "name": request.name,
            "description": request.description,
            "nodes": request.nodes,
            "edges": request.edges,
        },
        lock_level=request.lock_level.value,
        allowed_parameters=request.allowed_parameters,
        customer_name=request.customer_name,
        expires_in_days=request.expires_in_days,
    )

    # 만료 시간 파싱
    from datetime import datetime as dt
    expires_at_str = session.get("expires_at", "")
    try:
        expires_at = dt.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        expires_at = dt.now()

    logger.info(f"[WorkflowSession] Created locked session: {session['session_id']} for {request.customer_name}")

    return WorkflowSessionResponse(
        session_id=session["session_id"],
        share_url=f"/customer/session/{session['session_id']}",
        access_token=session["access_token"],
        expires_at=expires_at,
        workflow_name=request.name,
    )


@router.get("/{session_id}/workflow", response_model=WorkflowSessionDetail)
async def get_session_workflow(
    session_id: str,
    access_token: Optional[str] = Query(default=None, description="접근 토큰"),
):
    """세션의 워크플로우 정의 조회 (잠금 상태 포함)

    Args:
        session_id: 세션 ID
        access_token: 접근 토큰 (선택)

    Returns:
        WorkflowSessionDetail: 워크플로우 정보
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 접근 권한 검증
    if not service.validate_session_access(session_id, access_token):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    # 만료 시간 파싱
    from datetime import datetime as dt
    expires_at_str = session.get("expires_at")
    expires_at = None
    if expires_at_str:
        try:
            expires_at = dt.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    return WorkflowSessionDetail(
        session_id=session_id,
        workflow_definition=session.get("workflow_definition"),
        workflow_locked=session.get("workflow_locked", False),
        lock_level=session.get("lock_level", "none"),
        allowed_parameters=session.get("allowed_parameters", []),
        customer_name=session.get("customer_name"),
        access_token=session.get("access_token"),
        expires_at=expires_at,
    )


@router.post("/{session_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_session_workflow(
    session_id: str,
    request: WorkflowExecuteRequest,
    access_token: Optional[str] = Query(default=None, description="접근 토큰"),
):
    """세션 워크플로우 실행

    Args:
        session_id: 세션 ID
        request: 워크플로우 실행 요청 (이미지 ID, 파라미터)
        access_token: 접근 토큰 (선택)

    Returns:
        WorkflowExecuteResponse: 실행 결과
    """
    service = get_session_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 접근 권한 검증
    if not service.validate_session_access(session_id, access_token):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    # 파라미터 수정 권한 검증
    if request.parameters:
        valid, error_msg = service.validate_parameter_modification(session_id, request.parameters)
        if not valid:
            raise HTTPException(status_code=403, detail=error_msg)

    # TODO: Gateway API로 워크플로우 실행 위임
    # 현재는 상태만 업데이트
    service.update_session(session_id, {"status": SessionStatus.DETECTING})

    execution_id = str(uuid.uuid4())

    logger.info(f"[WorkflowSession] Executing workflow for session {session_id}, images: {len(request.image_ids)}")

    return WorkflowExecuteResponse(
        execution_id=execution_id,
        session_id=session_id,
        status="running",
        image_count=len(request.image_ids),
        message="워크플로우 실행이 시작되었습니다",
    )
