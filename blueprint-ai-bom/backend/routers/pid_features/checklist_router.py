"""P&ID Design Checklist Router

설계 체크리스트 검사 엔드포인트
"""

import os
import time
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
import httpx

from schemas.pid_features import (
    ChecklistStatus,
    ChecklistItem,
    ChecklistResponse,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["P&ID Checklist"])

# Configuration
DESIGN_CHECKER_URL = os.getenv("DESIGN_CHECKER_URL", "http://design-checker-api:5019")

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


@router.post("/{session_id}/checklist/check", response_model=ChecklistResponse)
async def check_design_checklist(
    session_id: str,
    rule_profile: str = Query(default="default", description="규칙 프로필 (default, bwms, chemical 등)"),
    enabled_rules: Optional[str] = Query(default=None, description="활성화할 규칙 (쉼표 구분)")
):
    """
    설계 체크리스트 검사

    P&ID 도면에 대해 설계 규칙을 자동 검증합니다.
    프로필에 따라 다른 규칙 세트가 적용됩니다.
    """
    start_time = time.time()
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    symbols = session.get("detections", [])
    connections = session.get("connections", [])
    texts = session.get("ocr_texts", [])

    if not symbols:
        logger.warning(f"Session {session_id}: No symbols detected, checklist may be incomplete")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            data = {
                "symbols": json.dumps(symbols),
                "connections": json.dumps(connections),
                "texts": json.dumps(texts),
                "enabled_rules": enabled_rules or "",
                "rule_profile": rule_profile
            }

            response = await client.post(
                f"{DESIGN_CHECKER_URL}/api/v1/check/bwms",
                data=data
            )

        if response.status_code != 200:
            logger.error(f"Design Checker error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Checklist check failed: {response.text}"
            )

        result = response.json()
        violations = result.get("data", {}).get("violations", [])

        checklist_items = []
        summary = {
            "Pass": 0,
            "Fail": 0,
            "N/A": 0,
            "Pending": 0,
            "Manual Required": 0
        }

        for idx, violation in enumerate(violations):
            status = ChecklistStatus.FAIL if violation.get("severity") == "error" else ChecklistStatus.PENDING
            summary[status.value] += 1

            checklist_item = ChecklistItem(
                id=f"check_{session_id[:8]}_{idx}",
                item_no=idx + 1,
                category=violation.get("category", "design"),
                description=violation.get("description", ""),
                description_ko=violation.get("rule_name", ""),
                auto_status=status,
                final_status=status,
                evidence=str(violation.get("affected_elements", [])),
                confidence=0.8 if status == ChecklistStatus.FAIL else 0.5,
                verification_status=VerificationStatus.PENDING
            )
            checklist_items.append(checklist_item)

        session_service.update_session(session_id, {
            "pid_checklist_items": [ci.model_dump() for ci in checklist_items],
            "pid_checklist_count": len(checklist_items)
        })

        processing_time = time.time() - start_time

        total = len(checklist_items)
        compliance_rate = (summary["Pass"] / total * 100) if total > 0 else 0.0

        return ChecklistResponse(
            session_id=session_id,
            items=checklist_items,
            total_count=len(checklist_items),
            summary=summary,
            compliance_rate=round(compliance_rate, 2),
            processing_time=round(processing_time, 3)
        )

    except httpx.RequestError as e:
        logger.error(f"Design Checker connection error: {e}")
        raise HTTPException(status_code=503, detail=f"Design Checker 서비스 연결 실패: {e}")
