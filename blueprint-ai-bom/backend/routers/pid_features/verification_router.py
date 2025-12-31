"""P&ID Verification Router

검증 엔드포인트 (공통)
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from schemas.pid_features import (
    PIDVerifyRequest,
    PIDBulkVerifyRequest,
    PIDVerificationQueue,
    VerificationStatus,
)
from services.active_learning_service import active_learning_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["P&ID Verification"])

# 서비스 의존성
_session_service = None


def set_session_service(session_service):
    """서비스 주입"""
    global _session_service
    _session_service = session_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# 필드 매핑 (공통)
FIELD_MAP = {
    "valve": "pid_valves",
    "equipment": "pid_equipment",
    "checklist_item": "pid_checklist_items",
    "deviation": "pid_deviations"
}


@router.get("/{session_id}/verify/queue", response_model=PIDVerificationQueue)
async def get_verification_queue(
    session_id: str,
    item_type: str = Query(..., description="항목 타입 (valve, equipment, checklist_item)")
):
    """
    검증 큐 조회

    우선순위 순으로 정렬된 검증 항목 반환
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    field_name = FIELD_MAP.get(item_type)
    if not field_name:
        raise HTTPException(status_code=400, detail=f"Invalid item_type: {item_type}")

    items = session.get(field_name, [])
    queue = active_learning_service.get_verification_queue(items, item_type)
    stats = active_learning_service.get_verification_stats(items, item_type)

    return PIDVerificationQueue(
        session_id=session_id,
        item_type=item_type,
        queue=[item.to_dict() for item in queue],
        stats=stats,
        thresholds=active_learning_service.thresholds
    )


@router.post("/{session_id}/verify")
async def verify_item(
    session_id: str,
    request: PIDVerifyRequest
):
    """
    개별 항목 검증
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    field_name = FIELD_MAP.get(request.item_type)
    if not field_name:
        raise HTTPException(status_code=400, detail=f"Invalid item_type: {request.item_type}")

    items = session.get(field_name, [])
    item_found = False

    for item in items:
        if item.get("id") == request.item_id:
            item_found = True

            if request.action == "approve":
                item["verification_status"] = VerificationStatus.APPROVED.value
            elif request.action == "reject":
                item["verification_status"] = VerificationStatus.REJECTED.value
            elif request.action == "modify":
                item["verification_status"] = VerificationStatus.MODIFIED.value
                if request.modified_data:
                    item.update(request.modified_data)

            item["modified_at"] = datetime.now().isoformat()
            item["notes"] = request.notes
            break

    if not item_found:
        raise HTTPException(status_code=404, detail=f"Item not found: {request.item_id}")

    session_service.update_session(session_id, {field_name: items})

    active_learning_service.log_verification(
        item_id=request.item_id,
        item_type=request.item_type,
        original_data={},
        user_action=request.action,
        modified_data=request.modified_data,
        session_id=session_id
    )

    return {
        "status": "success",
        "session_id": session_id,
        "item_id": request.item_id,
        "action": request.action
    }


@router.post("/{session_id}/verify/bulk")
async def bulk_verify_items(
    session_id: str,
    request: PIDBulkVerifyRequest
):
    """
    일괄 검증
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    field_name = FIELD_MAP.get(request.item_type)
    if not field_name:
        raise HTTPException(status_code=400, detail=f"Invalid item_type: {request.item_type}")

    items = session.get(field_name, [])
    updated_count = 0

    for item in items:
        if item.get("id") in request.item_ids:
            if request.action == "approve":
                item["verification_status"] = VerificationStatus.APPROVED.value
            elif request.action == "reject":
                item["verification_status"] = VerificationStatus.REJECTED.value

            item["modified_at"] = datetime.now().isoformat()
            updated_count += 1

    session_service.update_session(session_id, {field_name: items})

    return {
        "status": "success",
        "session_id": session_id,
        "updated_count": updated_count,
        "action": request.action
    }
