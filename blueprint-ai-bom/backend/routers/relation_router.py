"""관계 추출 API (Phase 2)

치수선 기반 치수-객체 관계 추출 API.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import time

from schemas.relation import (
    DimensionRelationSchema,
    RelationExtractionRequest,
    RelationExtractionResult,
    RelationUpdateRequest,
    BulkRelationUpdateRequest,
    RelationStatistics,
)
from services.dimension_relation_service import DimensionRelationService

router = APIRouter(prefix="/relations", tags=["Relations"])

# 서비스 인스턴스
relation_service = DimensionRelationService()

# 의존성 주입을 위한 서비스 참조
_session_service = None
_line_detector_service = None


def set_relation_services(session_service, line_detector_service=None):
    """서비스 주입"""
    global _session_service, _line_detector_service
    _session_service = session_service
    _line_detector_service = line_detector_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# ==================== Endpoints ====================

@router.post("/extract/{session_id}", response_model=RelationExtractionResult)
async def extract_relations(
    session_id: str,
    use_lines: bool = True
) -> RelationExtractionResult:
    """
    치수-객체 관계 추출

    치수선 추적 기반으로 치수와 심볼 간의 관계를 추출합니다.

    **추출 방법 (우선순위):**
    1. dimension_line: 치수선 추적 (~95% 신뢰도)
    2. extension_line: 연장선 추적 (~85% 신뢰도)
    3. proximity: 근접성 기반 (~60% 신뢰도)

    Args:
        session_id: 세션 ID
        use_lines: 선 검출 결과 사용 여부

    Returns:
        관계 추출 결과
    """
    start_time = time.time()
    session_service = get_session_service()

    # 세션 조회
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 치수 및 검출 결과 가져오기
    dimensions = session.get("dimensions", [])
    detections = session.get("detections", [])
    lines = session.get("lines", []) if use_lines else []

    if not dimensions:
        return RelationExtractionResult(
            session_id=session_id,
            relations=[],
            statistics={"message": "치수 데이터가 없습니다"},
            processing_time_ms=0
        )

    # 관계 추출
    relations = relation_service.extract_relations(
        dimensions=dimensions,
        symbols=detections,
        lines=lines
    )

    # 통계 계산
    statistics = _calculate_statistics(relations)

    # 세션에 관계 저장
    session_service.update_session(session_id, {
        "relations": relations
    })

    processing_time = (time.time() - start_time) * 1000

    return RelationExtractionResult(
        session_id=session_id,
        relations=[DimensionRelationSchema(**r) for r in relations],
        statistics=statistics,
        processing_time_ms=processing_time
    )


@router.get("/{session_id}", response_model=RelationExtractionResult)
async def get_relations(session_id: str) -> RelationExtractionResult:
    """
    세션의 관계 목록 조회
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    relations = session.get("relations", [])
    statistics = _calculate_statistics(relations)

    return RelationExtractionResult(
        session_id=session_id,
        relations=[DimensionRelationSchema(**r) for r in relations],
        statistics=statistics,
        processing_time_ms=0
    )


@router.put("/{session_id}/{relation_id}")
async def update_relation(
    session_id: str,
    relation_id: str,
    update: RelationUpdateRequest
) -> Dict[str, Any]:
    """
    관계 수동 수정

    사용자가 잘못된 관계를 수정할 때 사용합니다.
    수동 수정된 관계는 method가 'manual'로 변경되고 신뢰도 100%가 됩니다.
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    relations = session.get("relations", [])

    # 관계 찾기
    relation_idx = None
    for idx, rel in enumerate(relations):
        if rel.get("id") == relation_id:
            relation_idx = idx
            break

    if relation_idx is None:
        raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다")

    # 업데이트
    if update.target_id is not None:
        relations[relation_idx]["target_id"] = update.target_id
    if update.target_type is not None:
        relations[relation_idx]["target_type"] = update.target_type
    if update.notes is not None:
        relations[relation_idx]["notes"] = update.notes

    # 수동 수정 표시
    relations[relation_idx]["method"] = "manual"
    relations[relation_idx]["confidence"] = 1.0

    # 저장
    session_service.update_session(session_id, {"relations": relations})

    return {
        "success": True,
        "relation": relations[relation_idx]
    }


@router.put("/{session_id}/bulk")
async def bulk_update_relations(
    session_id: str,
    request: BulkRelationUpdateRequest
) -> Dict[str, Any]:
    """
    관계 일괄 수정
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    relations = session.get("relations", [])
    relation_map = {r.get("id"): idx for idx, r in enumerate(relations)}

    updated_count = 0
    for update in request.updates:
        if update.relation_id in relation_map:
            idx = relation_map[update.relation_id]

            if update.target_id is not None:
                relations[idx]["target_id"] = update.target_id
            if update.target_type is not None:
                relations[idx]["target_type"] = update.target_type
            if update.notes is not None:
                relations[idx]["notes"] = update.notes

            relations[idx]["method"] = "manual"
            relations[idx]["confidence"] = 1.0
            updated_count += 1

    session_service.update_session(session_id, {"relations": relations})

    return {
        "success": True,
        "updated_count": updated_count
    }


@router.delete("/{session_id}/{relation_id}")
async def delete_relation(session_id: str, relation_id: str) -> Dict[str, Any]:
    """
    관계 삭제
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    relations = session.get("relations", [])
    original_count = len(relations)

    relations = [r for r in relations if r.get("id") != relation_id]

    if len(relations) == original_count:
        raise HTTPException(status_code=404, detail="관계를 찾을 수 없습니다")

    session_service.update_session(session_id, {"relations": relations})

    return {
        "success": True,
        "deleted_id": relation_id
    }


@router.get("/{session_id}/statistics", response_model=RelationStatistics)
async def get_relation_statistics(session_id: str) -> RelationStatistics:
    """
    관계 추출 통계 조회
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    relations = session.get("relations", [])
    stats = _calculate_statistics(relations)

    return RelationStatistics(
        total=stats.get("total", 0),
        by_method=stats.get("by_method", {}),
        by_confidence=stats.get("by_confidence", {}),
        linked_count=stats.get("linked_count", 0),
        unlinked_count=stats.get("unlinked_count", 0)
    )


@router.post("/{session_id}/link/{dimension_id}/{target_id}")
async def link_dimension_to_target(
    session_id: str,
    dimension_id: str,
    target_id: str
) -> Dict[str, Any]:
    """
    치수를 특정 대상에 수동 연결

    UI에서 드래그&드롭으로 연결할 때 사용합니다.
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    relations = session.get("relations", [])
    detections = session.get("detections", [])

    # 대상 심볼 찾기
    target_symbol = None
    for det in detections:
        if det.get("id") == target_id:
            target_symbol = det
            break

    # 기존 관계 찾기 또는 새로 생성
    relation_idx = None
    for idx, rel in enumerate(relations):
        if rel.get("dimension_id") == dimension_id:
            relation_idx = idx
            break

    import uuid

    if relation_idx is not None:
        # 기존 관계 업데이트
        relations[relation_idx]["target_id"] = target_id
        relations[relation_idx]["target_type"] = "symbol"
        relations[relation_idx]["target_bbox"] = target_symbol.get("bbox") if target_symbol else None
        relations[relation_idx]["method"] = "manual"
        relations[relation_idx]["confidence"] = 1.0
        relations[relation_idx]["notes"] = "수동 연결됨"
    else:
        # 새 관계 생성
        new_relation = {
            "id": f"rel_{uuid.uuid4().hex[:8]}",
            "dimension_id": dimension_id,
            "target_type": "symbol",
            "target_id": target_id,
            "target_bbox": target_symbol.get("bbox") if target_symbol else None,
            "relation_type": "distance",
            "method": "manual",
            "confidence": 1.0,
            "direction": None,
            "notes": "수동 연결됨"
        }
        relations.append(new_relation)

    session_service.update_session(session_id, {"relations": relations})

    return {
        "success": True,
        "dimension_id": dimension_id,
        "target_id": target_id
    }


# ==================== Helper Functions ====================

def _calculate_statistics(relations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """관계 목록에서 통계 계산"""
    total = len(relations)

    if total == 0:
        return {
            "total": 0,
            "by_method": {},
            "by_confidence": {"high": 0, "medium": 0, "low": 0},
            "linked_count": 0,
            "unlinked_count": 0
        }

    by_method = {}
    high_conf = 0
    medium_conf = 0
    low_conf = 0
    linked = 0
    unlinked = 0

    for rel in relations:
        # 방법별 카운트
        method = rel.get("method", "proximity")
        by_method[method] = by_method.get(method, 0) + 1

        # 신뢰도별 카운트
        conf = rel.get("confidence", 0)
        if conf >= 0.85:
            high_conf += 1
        elif conf >= 0.6:
            medium_conf += 1
        else:
            low_conf += 1

        # 연결 상태
        if rel.get("target_id"):
            linked += 1
        else:
            unlinked += 1

    return {
        "total": total,
        "by_method": by_method,
        "by_confidence": {
            "high": high_conf,
            "medium": medium_conf,
            "low": low_conf
        },
        "linked_count": linked,
        "unlinked_count": unlinked
    }
