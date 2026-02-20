"""Agent Verification Router

Multimodal LLM Agent 전용 검증 API
- 크롭/컨텍스트/참조 이미지를 base64로 제공
- Playwright 자동화 친화적 응답 구조
- symbol(검출) + dimension(치수) 모두 지원
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


def _get_items(session: dict, item_type: str) -> list:
    """item_type에 따라 detections 또는 dimensions 반환"""
    if item_type == "dimension":
        return session.get("dimensions", [])
    return session.get("detections", [])


def _find_item(items: list, item_id: str) -> Optional[dict]:
    """ID로 항목 찾기"""
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


# ==================== Request/Response Models ====================

class AgentDecisionRequest(BaseModel):
    action: str  # "approve" | "reject" | "modify"
    modified_class: Optional[str] = None  # symbol 수정 시
    modified_value: Optional[str] = None  # dimension 값 수정
    modified_unit: Optional[str] = None  # dimension 단위 수정 (mm, °, μm)
    modified_type: Optional[str] = None  # dimension_type 수정 (length, gdt, angle, ...)
    modified_tolerance: Optional[str] = None  # 공차 수정
    reject_reason: Optional[str] = None  # 거부 사유 (not_dimension, garbage, duplicate)


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
    item_type: "symbol" (검출) 또는 "dimension" (치수)
    """
    session_service, crop_service = _get_services()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    items = _get_items(session, item_type)

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
        d = item.data
        entry = {
            "id": item.id,
            "confidence": item.confidence,
            "priority": item.priority.value,
            "reason": item.reason,
            "bbox": d.get("bbox", {}),
            "crop_url": f"/verification/agent/item/{session_id}/{item.id}?item_type={item_type}",
        }
        if item_type == "dimension":
            entry["value"] = d.get("value", "")
            entry["unit"] = d.get("unit", "mm")
            entry["dimension_type"] = d.get("dimension_type", "")
            entry["tolerance"] = d.get("tolerance")
        else:
            entry["class_name"] = d.get("class_name", "")
        queue_items.append(entry)

    return {
        "session_id": session_id,
        "item_type": item_type,
        "drawing_type": drawing_type,
        "queue": queue_items,
        "total_count": len(queue_items),
        "stats": stats,
    }


@router.get("/item/{session_id}/{item_id}")
async def get_agent_item(session_id: str, item_id: str, item_type: str = "symbol"):
    """
    단일 항목 상세 (base64 이미지 포함)

    crop, context 이미지를 base64로 제공
    symbol: + reference 이미지
    dimension: + value/unit/tolerance 메타데이터
    """
    session_service, crop_service = _get_services()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    items = _get_items(session, item_type)
    item = _find_item(items, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다")

    # 이미지 생성
    crop_bytes = crop_service.get_detection_crop(session_id, item_id, item_type=item_type)
    context_bytes = crop_service.get_context_image(session_id, item_id, item_type=item_type)

    crop_b64 = base64.b64encode(crop_bytes).decode() if crop_bytes else None
    context_b64 = base64.b64encode(context_bytes).decode() if context_bytes else None

    drawing_type = session.get("drawing_type", "electrical")

    # 공통 응답
    response = {
        "session_id": session_id,
        "item_id": item_id,
        "item_type": item_type,
        "confidence": item.get("confidence", 0),
        "bbox": item.get("bbox", {}),
        "verification_status": item.get("verification_status", "pending"),
        "crop_image": crop_b64,
        "context_image": context_b64,
        "metadata": {
            "model_id": item.get("model_id", ""),
            "drawing_type": drawing_type,
        },
    }

    if item_type == "dimension":
        response["value"] = item.get("value", "")
        response["raw_text"] = item.get("raw_text", "")
        response["unit"] = item.get("unit", "mm")
        response["tolerance"] = item.get("tolerance")
        response["dimension_type"] = item.get("dimension_type", "")
        response["linked_to"] = item.get("linked_to")
        response["reference_images"] = []
    else:
        class_name = item.get("class_name", "")
        response["class_name"] = class_name
        response["metadata"]["class_id"] = item.get("class_id")
        ref_bytes_list = crop_service.get_reference_images(class_name, drawing_type)
        response["reference_images"] = [
            base64.b64encode(rb).decode() for rb in ref_bytes_list
        ]

    return response


@router.post("/decide/{session_id}/{item_id}")
async def agent_decide(
    session_id: str,
    item_id: str,
    request: AgentDecisionRequest,
    item_type: str = "symbol",
):
    """
    Agent 검증 결정

    approve/reject/modify 중 하나 선택
    symbol: modify 시 modified_class 필수
    dimension: modify 시 modified_value 필수
    """
    session_service, crop_service = _get_services()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if request.action not in ("approve", "reject", "modify"):
        raise HTTPException(status_code=400, detail="action은 approve/reject/modify 중 하나여야 합니다")

    if request.action == "modify":
        if item_type == "dimension":
            has_any = any([request.modified_value, request.modified_unit, request.modified_type, request.modified_tolerance])
            if not has_any:
                raise HTTPException(status_code=400, detail="dimension modify 시 수정 필드가 하나 이상 필요합니다")
        elif not request.modified_class:
            raise HTTPException(status_code=400, detail="symbol modify 시 modified_class 필수")

    items = _get_items(session, item_type)
    item = _find_item(items, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다")

    original_data = item.copy()
    status_map = {"approve": "approved", "reject": "rejected", "modify": "modified"}
    status = status_map.get(request.action, request.action + "d")

    if item_type == "dimension":
        # dimension: 직접 업데이트 (update_verification은 detections 전용)
        item["verification_status"] = status
        item["verified_by"] = "agent"
        if request.action == "reject" and request.reject_reason:
            item["reject_reason"] = request.reject_reason
        if request.action == "modify":
            if request.modified_value:
                item["modified_value"] = request.modified_value
            if request.modified_unit:
                item["unit"] = request.modified_unit
            if request.modified_type:
                item["dimension_type"] = request.modified_type
            if request.modified_tolerance is not None:
                item["tolerance"] = request.modified_tolerance or None
        session_service.update_session(session_id, {"dimensions": items})
    else:
        # symbol: update_verification 사용
        modified_class_name = request.modified_class if request.action == "modify" else None
        session_service.update_verification(
            session_id=session_id,
            detection_id=item_id,
            status=status,
            modified_class_name=modified_class_name,
        )
        # verified_by 플래그 추가
        refreshed = session_service.get_session(session_id)
        for det in refreshed.get("detections", []):
            if det.get("id") == item_id:
                if det.get("verified_by") != "agent":
                    det["verified_by"] = "agent"
                    session_service.update_session(session_id, {"detections": refreshed["detections"]})
                break

    # Active Learning 로그
    modified_data = None
    if request.action == "reject" and request.reject_reason:
        modified_data = {"reject_reason": request.reject_reason}
    elif request.action == "modify":
        if item_type == "dimension":
            modified_data = {}
            if request.modified_value:
                modified_data["modified_value"] = request.modified_value
            if request.modified_unit:
                modified_data["modified_unit"] = request.modified_unit
            if request.modified_type:
                modified_data["modified_type"] = request.modified_type
            if request.modified_tolerance is not None:
                modified_data["modified_tolerance"] = request.modified_tolerance
        else:
            modified_data = {"modified_class_name": request.modified_class}

    active_learning_service.log_verification(
        item_id=item_id,
        item_type=item_type,
        original_data=original_data,
        user_action=status,
        modified_data=modified_data,
        session_id=session_id,
    )

    # 다음 항목 조회
    refreshed = session_service.get_session(session_id)
    all_items = _get_items(refreshed, item_type)
    pending = [d for d in all_items if d.get("verification_status", "pending") == "pending"]
    stats = active_learning_service.get_verification_stats(all_items, item_type)

    next_id = None
    if pending:
        queue = active_learning_service.get_verification_queue(pending, item_type)
        if queue:
            next_id = queue[0].id

    return AgentDecisionResponse(
        success=True,
        next_item_id=next_id,
        remaining_count=len(pending),
        stats=stats,
    )
