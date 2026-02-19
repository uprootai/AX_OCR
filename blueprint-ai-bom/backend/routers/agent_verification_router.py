"""Agent Verification Router

Multimodal LLM Agent 전용 검증 API
- 크롭/컨텍스트/참조 이미지를 base64로 제공
- Playwright 자동화 친화적 응답 구조
"""
import base64
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.active_learning_service import active_learning_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verification/agent", tags=["Verification - Agent"])

# 서비스 인스턴스 (DI 패턴)
_session_service = None
_crop_service = None


def set_agent_verification_services(session_service, crop_service):
    """서비스 주입"""
    global _session_service, _crop_service
    _session_service = session_service
    _crop_service = crop_service


def _get_services():
    if _session_service is None or _crop_service is None:
        raise HTTPException(status_code=500, detail="Agent verification services not initialized")
    return _session_service, _crop_service


# ==================== Request/Response Models ====================

class AgentDecisionRequest(BaseModel):
    action: str  # "approve" | "reject" | "modify"
    modified_class: Optional[str] = None


class AgentDecisionResponse(BaseModel):
    success: bool
    next_item_id: Optional[str] = None
    remaining_count: int = 0
    stats: dict = {}


# ==================== Endpoints ====================

@router.get("/queue/{session_id}")
async def get_agent_queue(session_id: str, item_type: str = "symbol"):
    """
    Agent용 검증 큐 조회

    pending 항목만 우선순위 정렬하여 반환
    각 항목에 crop_url, reference_url 포함
    """
    session_service, crop_service = _get_services()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if item_type == "dimension":
        items = session.get("dimensions", [])
    else:
        items = session.get("detections", [])

    # 검증 큐 생성 (pending만 필터)
    queue = active_learning_service.get_verification_queue(items, item_type)
    pending_queue = [
        item for item in queue
        if item.data.get("verification_status", "pending") == "pending"
    ]

    stats = active_learning_service.get_verification_stats(items, item_type)
    drawing_type = session.get("drawing_type", "electrical")

    # 응답 구성
    queue_items = []
    for item in pending_queue:
        det = item.data
        queue_items.append({
            "id": item.id,
            "class_name": det.get("class_name", ""),
            "confidence": item.confidence,
            "priority": item.priority.value,
            "reason": item.reason,
            "bbox": det.get("bbox", {}),
            "crop_url": f"/verification/agent/item/{session_id}/{item.id}",
        })

    return {
        "session_id": session_id,
        "drawing_type": drawing_type,
        "queue": queue_items,
        "total_count": len(queue_items),
        "stats": stats,
    }


@router.get("/item/{session_id}/{detection_id}")
async def get_agent_item(session_id: str, detection_id: str):
    """
    단일 항목 상세 (base64 이미지 포함)

    crop, context, references 이미지를 base64로 제공
    """
    session_service, crop_service = _get_services()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 검출 항목 찾기
    detection = None
    for det in session.get("detections", []):
        if det.get("id") == detection_id:
            detection = det
            break

    if not detection:
        raise HTTPException(status_code=404, detail="검출 항목을 찾을 수 없습니다")

    # 이미지 생성
    crop_bytes = crop_service.get_detection_crop(session_id, detection_id)
    context_bytes = crop_service.get_context_image(session_id, detection_id)

    class_name = detection.get("class_name", "")
    drawing_type = session.get("drawing_type", "electrical")
    ref_bytes_list = crop_service.get_reference_images(class_name, drawing_type)

    # base64 인코딩
    crop_b64 = base64.b64encode(crop_bytes).decode() if crop_bytes else None
    context_b64 = base64.b64encode(context_bytes).decode() if context_bytes else None
    references_b64 = [
        base64.b64encode(rb).decode() for rb in ref_bytes_list
    ]

    return {
        "session_id": session_id,
        "detection_id": detection_id,
        "class_name": class_name,
        "confidence": detection.get("confidence", 0),
        "bbox": detection.get("bbox", {}),
        "verification_status": detection.get("verification_status", "pending"),
        "crop_image": crop_b64,
        "context_image": context_b64,
        "reference_images": references_b64,
        "metadata": {
            "class_id": detection.get("class_id"),
            "model_id": detection.get("model_id", ""),
            "drawing_type": drawing_type,
        },
    }


@router.post("/decide/{session_id}/{detection_id}")
async def agent_decide(
    session_id: str,
    detection_id: str,
    request: AgentDecisionRequest,
):
    """
    Agent 검증 결정

    approve/reject/modify 중 하나 선택
    modify 시 modified_class 필수
    """
    session_service, crop_service = _get_services()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if request.action not in ("approve", "reject", "modify"):
        raise HTTPException(status_code=400, detail="action은 approve/reject/modify 중 하나여야 합니다")

    if request.action == "modify" and not request.modified_class:
        raise HTTPException(status_code=400, detail="modify 시 modified_class 필수")

    # 검출 항목 확인
    detection = None
    for det in session.get("detections", []):
        if det.get("id") == detection_id:
            detection = det
            break
    if not detection:
        raise HTTPException(status_code=404, detail="검출 항목을 찾을 수 없습니다")

    # 검증 상태 결정
    status = "modified" if request.action == "modify" else request.action + "d"  # approved/rejected
    modified_class_name = request.modified_class if request.action == "modify" else None

    # session_service.update_verification 호출
    session_service.update_verification(
        session_id=session_id,
        detection_id=detection_id,
        status=status,
        modified_class_name=modified_class_name,
    )

    # verified_by 플래그 추가 (update_verification 이후 세션을 한 번만 다시 저장)
    refreshed_for_flag = session_service.get_session(session_id)
    for det in refreshed_for_flag.get("detections", []):
        if det.get("id") == detection_id:
            if det.get("verified_by") != "agent":
                det["verified_by"] = "agent"
                session_service.update_session(session_id, {"detections": refreshed_for_flag["detections"]})
            break

    # Active Learning 로그
    active_learning_service.log_verification(
        item_id=detection_id,
        item_type="symbol",
        original_data=detection,
        user_action=status,
        modified_data={"modified_class_name": modified_class_name} if modified_class_name else None,
        session_id=session_id,
    )

    # 다음 항목 조회
    refreshed = session_service.get_session(session_id)
    detections = refreshed.get("detections", [])
    pending = [
        d for d in detections
        if d.get("verification_status", "pending") == "pending"
    ]
    stats = active_learning_service.get_verification_stats(detections, "symbol")

    next_id = None
    if pending:
        queue = active_learning_service.get_verification_queue(pending, "symbol")
        if queue:
            next_id = queue[0].id

    return AgentDecisionResponse(
        success=True,
        next_item_id=next_id,
        remaining_count=len(pending),
        stats=stats,
    )
