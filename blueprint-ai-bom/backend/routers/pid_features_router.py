"""P&ID 분석 기능 라우터

P&ID 도면 분석을 위한 Human-in-the-Loop 워크플로우 API

기능:
- Valve Detection: P&ID 밸브 태그 검출
- Equipment Detection: 장비 태그 검출 및 목록화
- Design Checklist: 설계 규칙 검증
- Deviation Analysis: 기준 대비 편차 분석 (향후)

워크플로우:
1. 세션 생성 (features: pid_valve_detection, pid_equipment_detection, pid_design_checklist)
2. 각 기능별 검출 실행
3. 검증 큐에서 검토/승인/수정
4. Excel 내보내기

구조:
이 파일은 서브 라우터를 통합하고 summary 엔드포인트를 제공합니다.
실제 기능은 routers/pid_features/ 디렉토리의 개별 라우터에 구현되어 있습니다.
"""

import logging
from typing import List, Dict

from fastapi import APIRouter, HTTPException

from routers.pid_features import (
    create_pid_features_router,
    set_session_service as set_sub_routers_service,
)

logger = logging.getLogger(__name__)

# 메인 라우터 생성
router = APIRouter(prefix="/pid-features", tags=["P&ID Features"])

# 서브 라우터 통합
_sub_router = create_pid_features_router()
router.include_router(_sub_router)

# 서비스 의존성
_session_service = None


def set_pid_features_service(session_service):
    """서비스 주입 (메인 + 서브 라우터)"""
    global _session_service
    _session_service = session_service
    # 서브 라우터에도 서비스 주입
    set_sub_routers_service(session_service)


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# =====================
# Summary
# =====================

@router.get("/{session_id}/summary")
async def get_pid_features_summary(session_id: str):
    """
    P&ID 분석 기능 요약
    """
    session_service = get_session_service()
    session = session_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    def count_by_status(items: List[Dict]) -> Dict[str, int]:
        counts = {"pending": 0, "approved": 0, "rejected": 0, "modified": 0, "total": len(items)}
        for item in items:
            status = item.get("verification_status", "pending")
            if status in counts:
                counts[status] += 1
        return counts

    valves = session.get("pid_valves", [])
    equipment = session.get("pid_equipment", [])
    checklist_items = session.get("pid_checklist_items", [])
    deviations = session.get("pid_deviations", [])

    return {
        "session_id": session_id,
        "features": session.get("features", []),
        "valve_detection": {
            "detected": len(valves) > 0,
            "counts": count_by_status(valves)
        },
        "equipment_detection": {
            "detected": len(equipment) > 0,
            "counts": count_by_status(equipment)
        },
        "design_checklist": {
            "detected": len(checklist_items) > 0,
            "counts": count_by_status(checklist_items)
        },
        "deviation_analysis": {
            "detected": len(deviations) > 0,
            "counts": count_by_status(deviations),
            "by_severity": {
                sev: sum(1 for d in deviations if d.get("severity") == sev)
                for sev in ["critical", "high", "medium", "low", "info"]
            }
        },
        "overall_progress": {
            "total_items": len(valves) + len(equipment) + len(checklist_items) + len(deviations),
            "verified_items": sum(
                1 for items in [valves, equipment, checklist_items, deviations]
                for item in items
                if item.get("verification_status") != "pending"
            )
        }
    }
