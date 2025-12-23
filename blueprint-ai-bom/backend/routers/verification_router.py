"""검증 API (Active Learning 통합)

우선순위 기반 검증 큐 관리 및 검증 결과 로깅
- 저신뢰 항목 우선 검증
- 고신뢰 항목 일괄 승인
- 검증 결과 로깅 (모델 재학습용)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.active_learning_service import (
    active_learning_service,
    ActiveLearningService,
    Priority
)

router = APIRouter(prefix="/verification", tags=["Verification"])

# 서비스 인스턴스 (DI 패턴)
_session_service = None


def set_verification_services(session_service):
    """서비스 주입"""
    global _session_service
    _session_service = session_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# ==================== Request/Response Models ====================

class VerificationAction(BaseModel):
    """검증 액션"""
    item_id: str
    item_type: str = Field(default="dimension", description="dimension 또는 symbol")
    action: str = Field(description="approved, rejected, modified")
    modified_data: Optional[Dict[str, Any]] = None
    review_time_seconds: Optional[float] = None


class BulkApproveRequest(BaseModel):
    """일괄 승인 요청"""
    item_ids: List[str]
    item_type: str = "dimension"


class ThresholdUpdateRequest(BaseModel):
    """임계값 업데이트"""
    auto_approve_threshold: Optional[float] = Field(None, ge=0.5, le=1.0)
    critical_threshold: Optional[float] = Field(None, ge=0.0, le=0.9)


# ==================== Endpoints ====================

@router.get("/queue/{session_id}")
async def get_verification_queue(
    session_id: str,
    item_type: str = "dimension"
) -> Dict[str, Any]:
    """
    검증 큐 조회

    우선순위 순으로 정렬된 검증 항목 반환:
    1. CRITICAL: 신뢰도 < 0.7 (최우선)
    2. HIGH: 심볼 연결 없음
    3. MEDIUM: 신뢰도 0.7-0.9
    4. LOW: 신뢰도 >= 0.9 (자동 승인 후보)
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 아이템 타입에 따라 데이터 조회
    if item_type == "dimension":
        items = session.get("dimensions", [])
    else:  # symbol
        items = session.get("detections", [])

    # 검증 큐 생성
    queue = active_learning_service.get_verification_queue(items, item_type)

    # 통계
    stats = active_learning_service.get_verification_stats(items, item_type)

    return {
        "session_id": session_id,
        "item_type": item_type,
        "queue": [item.to_dict() for item in queue],
        "stats": stats,
        "thresholds": active_learning_service.thresholds
    }


@router.get("/stats/{session_id}")
async def get_verification_stats(
    session_id: str,
    item_type: str = "dimension"
) -> Dict[str, Any]:
    """검증 통계 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if item_type == "dimension":
        items = session.get("dimensions", [])
    else:
        items = session.get("detections", [])

    stats = active_learning_service.get_verification_stats(items, item_type)

    return {
        "session_id": session_id,
        "item_type": item_type,
        "stats": stats,
        "thresholds": active_learning_service.thresholds
    }


@router.get("/auto-approve-candidates/{session_id}")
async def get_auto_approve_candidates(
    session_id: str,
    item_type: str = "dimension"
) -> Dict[str, Any]:
    """
    자동 승인 후보 조회

    신뢰도 >= 0.9인 pending 상태 항목들
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if item_type == "dimension":
        items = session.get("dimensions", [])
    else:
        items = session.get("detections", [])

    candidates = active_learning_service.get_auto_approve_candidates(items)

    # 후보 항목의 상세 정보
    candidate_items = [
        item for item in items
        if item.get("id") in candidates
    ]

    return {
        "session_id": session_id,
        "item_type": item_type,
        "candidates": candidates,
        "candidate_items": candidate_items,
        "count": len(candidates),
        "threshold": active_learning_service.thresholds['auto_approve']
    }


@router.post("/verify/{session_id}")
async def verify_item(
    session_id: str,
    action: VerificationAction
) -> Dict[str, Any]:
    """
    단일 항목 검증

    검증 결과를 세션에 저장하고 로그 기록
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 아이템 조회
    if action.item_type == "dimension":
        items = session.get("dimensions", [])
    else:
        items = session.get("detections", [])

    # 해당 아이템 찾기
    item_idx = None
    original_item = None
    for idx, item in enumerate(items):
        if item.get("id") == action.item_id:
            item_idx = idx
            original_item = item.copy()
            break

    if item_idx is None:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다")

    # 검증 상태 업데이트
    items[item_idx]["verification_status"] = action.action

    # 수정된 데이터 적용
    if action.modified_data:
        for key, value in action.modified_data.items():
            if key.startswith("modified_"):
                items[item_idx][key] = value

    # 세션 업데이트
    if action.item_type == "dimension":
        session_service.update_session(session_id, {"dimensions": items})
    else:
        session_service.update_session(session_id, {"detections": items})

    # 검증 로그 기록
    active_learning_service.log_verification(
        item_id=action.item_id,
        item_type=action.item_type,
        original_data=original_item,
        user_action=action.action,
        modified_data=action.modified_data,
        session_id=session_id,
        review_time_seconds=action.review_time_seconds
    )

    return {
        "session_id": session_id,
        "item_id": action.item_id,
        "action": action.action,
        "success": True,
        "message": f"항목 '{action.item_id}' 검증 완료 ({action.action})"
    }


@router.post("/bulk-approve/{session_id}")
async def bulk_approve(
    session_id: str,
    request: BulkApproveRequest
) -> Dict[str, Any]:
    """
    고신뢰 항목 일괄 승인

    자동 승인 후보들을 한 번에 승인 처리
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if request.item_type == "dimension":
        items = session.get("dimensions", [])
    else:
        items = session.get("detections", [])

    approved_count = 0
    for item in items:
        if item.get("id") in request.item_ids:
            original_status = item.get("verification_status", "pending")
            if original_status == "pending":
                item["verification_status"] = "approved"
                approved_count += 1

                # 로그 기록
                active_learning_service.log_verification(
                    item_id=item["id"],
                    item_type=request.item_type,
                    original_data=item,
                    user_action="approved",
                    session_id=session_id
                )

    # 세션 업데이트
    if request.item_type == "dimension":
        session_service.update_session(session_id, {"dimensions": items})
    else:
        session_service.update_session(session_id, {"detections": items})

    return {
        "session_id": session_id,
        "item_type": request.item_type,
        "requested_count": len(request.item_ids),
        "approved_count": approved_count,
        "success": True,
        "message": f"{approved_count}개 항목 일괄 승인 완료"
    }


@router.post("/auto-approve/{session_id}")
async def auto_approve_all(
    session_id: str,
    item_type: str = "dimension"
) -> Dict[str, Any]:
    """
    모든 자동 승인 후보 승인

    신뢰도 >= 0.9인 모든 pending 항목 자동 승인
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    if item_type == "dimension":
        items = session.get("dimensions", [])
    else:
        items = session.get("detections", [])

    # 자동 승인 후보 조회
    candidates = active_learning_service.get_auto_approve_candidates(items)

    # 일괄 승인 요청 생성
    request = BulkApproveRequest(item_ids=candidates, item_type=item_type)

    # 일괄 승인 실행
    return await bulk_approve(session_id, request)


@router.get("/logs/{session_id}")
async def get_verification_logs(
    session_id: str,
    action_filter: Optional[str] = None
) -> Dict[str, Any]:
    """검증 로그 조회"""
    logs = active_learning_service.get_training_data(
        session_id=session_id,
        action_filter=action_filter
    )

    return {
        "session_id": session_id,
        "logs": logs,
        "count": len(logs)
    }


@router.put("/thresholds")
async def update_thresholds(
    request: ThresholdUpdateRequest
) -> Dict[str, Any]:
    """
    검증 임계값 업데이트

    - auto_approve_threshold: 자동 승인 최소 신뢰도 (기본 0.9)
    - critical_threshold: 크리티컬 우선순위 임계값 (기본 0.7)
    """
    updated = {}

    if request.auto_approve_threshold is not None:
        active_learning_service.thresholds['auto_approve'] = request.auto_approve_threshold
        updated['auto_approve'] = request.auto_approve_threshold

    if request.critical_threshold is not None:
        active_learning_service.thresholds['critical'] = request.critical_threshold
        updated['critical'] = request.critical_threshold

    return {
        "updated": updated,
        "current_thresholds": active_learning_service.thresholds
    }


@router.get("/thresholds")
async def get_thresholds() -> Dict[str, Any]:
    """현재 임계값 조회"""
    return {
        "thresholds": active_learning_service.thresholds
    }


@router.get("/training-data")
async def get_training_data(
    session_id: Optional[str] = None,
    action_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    모델 재학습용 데이터 조회

    검증 로그에서 학습용 데이터 추출
    """
    data = active_learning_service.get_training_data(
        session_id=session_id,
        action_filter=action_filter
    )

    # 통계
    action_counts = {}
    for item in data:
        action = item['action']
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "data": data,
        "count": len(data),
        "action_counts": action_counts,
        "filters": {
            "session_id": session_id,
            "action_filter": action_filter
        }
    }
