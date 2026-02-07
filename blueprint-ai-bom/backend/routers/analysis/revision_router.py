"""Revision Router - 리비전 비교 API (장기 로드맵)

longterm_router.py에서 분리된 리비전 비교 기능:
- 리비전 비교 실행 (POST /analysis/revision/compare)
- 비교 결과 조회 (GET /analysis/revision/{session_id})
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging
import time
import uuid

from services.revision_comparator import revision_comparator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Revision Comparison"])

# Session 서비스 의존성
_session_service = None


def set_revision_services(session_service):
    """세션 서비스 설정"""
    global _session_service
    _session_service = session_service


def get_session_service():
    """세션 서비스 인스턴스 가져오기 (지연 초기화)"""
    global _session_service
    if _session_service is None:
        from services.session_service import SessionService
        _session_service = SessionService()
    return _session_service


@router.post("/revision/compare")
async def compare_revisions(request: Dict[str, Any]) -> Dict[str, Any]:
    """두 도면 리비전 비교

    이미지 기반 구조적 비교 (SSIM) + 세션 데이터 비교 + VLM 지능형 비교를 수행합니다.

    Request body:
    - session_id_old: 이전 리비전 세션 ID
    - session_id_new: 새 리비전 세션 ID
    - config: 비교 설정 (선택)
        - use_vlm: VLM 기반 비교 사용 (기본: False)
        - compare_dimensions: 치수 비교 (기본: True)
        - compare_symbols: 심볼 비교 (기본: True)
        - compare_notes: 노트 비교 (기본: True)

    환경변수:
    - OPENAI_API_KEY: VLM 비교 시 필요
    """
    start_time = time.time()

    session_id_old = request.get("session_id_old")
    session_id_new = request.get("session_id_new")
    config = request.get("config", {})

    if not session_id_old or not session_id_new:
        raise HTTPException(status_code=400, detail="session_id_old와 session_id_new가 필요합니다")

    session_service = get_session_service()

    session_old = session_service.get_session(session_id_old)
    session_new = session_service.get_session(session_id_new)

    if not session_old:
        raise HTTPException(status_code=404, detail="이전 리비전 세션을 찾을 수 없습니다")
    if not session_new:
        raise HTTPException(status_code=404, detail="새 리비전 세션을 찾을 수 없습니다")

    # 리비전 비교 실행
    try:
        comparison_result = await revision_comparator.compare_revisions(
            session_old=session_old,
            session_new=session_new,
            config=config
        )

        # 변경 사항을 직렬화 가능한 형태로 변환
        changes = [
            {
                "id": c.id,
                "change_type": c.change_type.value,
                "category": c.category.value,
                "description": c.description,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "bbox_old": c.bbox_old,
                "bbox_new": c.bbox_new,
                "confidence": c.confidence,
                "severity": c.severity.value,
                "item_id": c.item_id,
            }
            for c in comparison_result.changes
        ]

        logger.info(
            f"[Revision] 비교 완료 - {comparison_result.total_changes}개 변경점, "
            f"유사도: {comparison_result.similarity_score:.2%}"
        )

    except Exception as e:
        logger.error(f"[Revision] 비교 실패: {e}")
        changes = []
        comparison_result = None

    processing_time = (time.time() - start_time) * 1000

    if comparison_result:
        result = {
            "comparison_id": comparison_result.comparison_id,
            "session_id_old": session_id_old,
            "session_id_new": session_id_new,
            "changes": changes,
            "total_changes": comparison_result.total_changes,
            "by_type": comparison_result.by_type,
            "by_category": comparison_result.by_category,
            "added_count": comparison_result.added_count,
            "removed_count": comparison_result.removed_count,
            "modified_count": comparison_result.modified_count,
            "similarity_score": comparison_result.similarity_score,
            "alignment_score": comparison_result.alignment_score,
            "diff_image_base64": comparison_result.diff_image_base64,
            "comparison_provider": comparison_result.provider,
            "processing_time_ms": processing_time,
        }
    else:
        result = {
            "comparison_id": str(uuid.uuid4()),
            "session_id_old": session_id_old,
            "session_id_new": session_id_new,
            "changes": [],
            "total_changes": 0,
            "by_type": {},
            "by_category": {},
            "added_count": 0,
            "removed_count": 0,
            "modified_count": 0,
            "similarity_score": 0.0,
            "alignment_score": 0.0,
            "diff_image_base64": None,
            "comparison_provider": "error",
            "processing_time_ms": processing_time,
        }

    # 새 세션에 비교 결과 저장
    session_service.update_session(session_id_new, {"revision_comparison": result})

    return result


@router.get("/revision/{session_id}")
async def get_revision_comparison(session_id: str) -> Dict[str, Any]:
    """리비전 비교 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session.get("revision_comparison", {
        "comparison_id": None,
        "session_id_old": None,
        "session_id_new": session_id,
        "changes": [],
        "total_changes": 0,
        "by_type": {},
        "by_category": {},
        "added_count": 0,
        "removed_count": 0,
        "modified_count": 0,
        "similarity_score": 0.0,
        "alignment_score": 0.0,
        "diff_image_base64": None,
        "comparison_provider": "none",
        "processing_time_ms": 0,
    })
