"""Detection Router - 검출 API 엔드포인트"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body

from schemas.detection import (
    DetectionConfig,
    DetectionResult,
    VerificationUpdate,
    BulkVerificationUpdate,
    ManualDetection,
)


router = APIRouter(prefix="/detection", tags=["detection"])


# 의존성 주입을 위한 전역 서비스
_detection_service = None
_session_service = None


def set_detection_service(detection_service, session_service):
    """서비스 인스턴스 설정"""
    global _detection_service, _session_service
    _detection_service = detection_service
    _session_service = session_service


def get_detection_service():
    """검출 서비스 의존성"""
    if _detection_service is None:
        raise HTTPException(status_code=500, detail="Detection service not initialized")
    return _detection_service


def get_session_service():
    """세션 서비스 의존성"""
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


@router.post("/{session_id}/detect", response_model=DetectionResult)
async def detect(session_id: str, config: Optional[DetectionConfig] = None):
    """이미지에서 객체 검출 실행"""
    detection_service = get_detection_service()
    session_service = get_session_service()

    # 세션 확인
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 상태 업데이트
    from schemas.session import SessionStatus
    session_service.update_status(session_id, SessionStatus.DETECTING)

    try:
        # 검출 실행
        result = detection_service.detect(
            image_path=session["file_path"],
            config=config
        )

        # 세션에 검출 결과 저장
        session_service.set_detections(
            session_id=session_id,
            detections=result["detections"],
            image_width=result["image_width"],
            image_height=result["image_height"]
        )

        return DetectionResult(
            session_id=session_id,
            **result
        )

    except Exception as e:
        session_service.update_status(
            session_id,
            SessionStatus.ERROR,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/detections")
async def get_detections(session_id: str):
    """세션의 검출 결과 조회"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return {
        "session_id": session_id,
        "detections": session.get("detections", []),
        "detection_count": session.get("detection_count", 0),
        "image_width": session.get("image_width"),
        "image_height": session.get("image_height"),
        "verification_status": session.get("verification_status", {}),
    }


@router.put("/{session_id}/verify")
async def verify_detection(session_id: str, update: VerificationUpdate):
    """단일 검출 검증 상태 업데이트"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 검출 ID 확인
    detection_ids = [d["id"] for d in session.get("detections", [])]
    if update.detection_id not in detection_ids:
        raise HTTPException(status_code=404, detail="검출 ID를 찾을 수 없습니다")

    # bbox를 dict로 변환
    modified_bbox = None
    if update.modified_bbox:
        modified_bbox = update.modified_bbox.model_dump()

    # 업데이트
    result = session_service.update_verification(
        session_id=session_id,
        detection_id=update.detection_id,
        status=update.status.value,
        modified_class_name=update.modified_class_name,
        modified_bbox=modified_bbox
    )

    return {
        "session_id": session_id,
        "detection_id": update.detection_id,
        "status": update.status.value,
        "verified_count": result.get("verified_count", 0),
        "approved_count": result.get("approved_count", 0),
        "rejected_count": result.get("rejected_count", 0),
    }


@router.put("/{session_id}/verify/bulk")
async def bulk_verify_detections(session_id: str, updates: BulkVerificationUpdate):
    """일괄 검출 검증 상태 업데이트"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    detection_ids = [d["id"] for d in session.get("detections", [])]
    results = []

    for update in updates.updates:
        if update.detection_id not in detection_ids:
            results.append({
                "detection_id": update.detection_id,
                "status": "error",
                "message": "검출 ID를 찾을 수 없습니다"
            })
            continue

        modified_bbox = None
        if update.modified_bbox:
            modified_bbox = update.modified_bbox.model_dump()

        session_service.update_verification(
            session_id=session_id,
            detection_id=update.detection_id,
            status=update.status.value,
            modified_class_name=update.modified_class_name,
            modified_bbox=modified_bbox
        )

        results.append({
            "detection_id": update.detection_id,
            "status": "updated"
        })

    # 최신 세션 정보
    session = session_service.get_session(session_id)

    return {
        "session_id": session_id,
        "results": results,
        "verified_count": session.get("verified_count", 0),
        "approved_count": session.get("approved_count", 0),
        "rejected_count": session.get("rejected_count", 0),
    }


@router.post("/{session_id}/manual")
async def add_manual_detection(session_id: str, detection: ManualDetection):
    """수동 검출 추가"""
    detection_service = get_detection_service()
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 수동 검출 생성
    new_detection = detection_service.add_manual_detection(
        class_name=detection.class_name,
        bbox=detection.bbox.model_dump()
    )

    # 세션에 추가
    detections = session.get("detections", [])
    detections.append(new_detection)

    verification_status = session.get("verification_status", {})
    verification_status[new_detection["id"]] = "manual"

    session_service.update_session(session_id, {
        "detections": detections,
        "detection_count": len(detections),
        "verification_status": verification_status,
        "approved_count": session.get("approved_count", 0) + 1,
    })

    return {
        "session_id": session_id,
        "detection": new_detection,
        "message": "수동 검출이 추가되었습니다"
    }


@router.delete("/{session_id}/detection/{detection_id}")
async def delete_detection(session_id: str, detection_id: str):
    """검출 삭제"""
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    detections = session.get("detections", [])
    verification_status = session.get("verification_status", {})

    # 검출 찾기 및 삭제
    new_detections = [d for d in detections if d["id"] != detection_id]

    if len(new_detections) == len(detections):
        raise HTTPException(status_code=404, detail="검출 ID를 찾을 수 없습니다")

    # verification_status에서도 삭제
    if detection_id in verification_status:
        del verification_status[detection_id]

    # 통계 재계산
    statuses = list(verification_status.values())
    verified_count = len([s for s in statuses if s != "pending"])
    approved_count = len([s for s in statuses if s in ("approved", "modified", "manual")])
    rejected_count = len([s for s in statuses if s == "rejected"])

    session_service.update_session(session_id, {
        "detections": new_detections,
        "detection_count": len(new_detections),
        "verification_status": verification_status,
        "verified_count": verified_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    })

    return {
        "session_id": session_id,
        "detection_id": detection_id,
        "message": "검출이 삭제되었습니다"
    }


@router.get("/classes")
async def get_class_names():
    """사용 가능한 클래스 이름 목록"""
    detection_service = get_detection_service()

    return {
        "classes": detection_service.get_class_names(),
        "mapping": detection_service.get_class_mapping()
    }
