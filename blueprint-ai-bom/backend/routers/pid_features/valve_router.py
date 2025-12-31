"""P&ID Valve Detection Router

밸브 검출 엔드포인트
"""

import os
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
import httpx

from schemas.pid_features import (
    ValveCategory,
    ValveItem,
    ValveDetectionResponse,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["P&ID Valve"])

# Configuration
PID_ANALYZER_URL = os.getenv("PID_ANALYZER_URL", "http://pid-analyzer-api:5018")

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


def _classify_valve_category(valve_id: str, valve_type: str) -> ValveCategory:
    """밸브 카테고리 분류"""
    valve_id_upper = valve_id.upper()
    valve_type_upper = valve_type.upper()

    # 제어 밸브
    if valve_type_upper in ["CV", "FCV", "PCV", "TCV", "LCV"]:
        return ValveCategory.CONTROL

    # 차단 밸브
    if valve_type_upper in ["XV", "BV", "GV", "IV"]:
        return ValveCategory.ISOLATION

    # 안전 밸브
    if valve_type_upper in ["SV", "PSV", "TSV"]:
        return ValveCategory.SAFETY

    # 체크 밸브
    if valve_type_upper in ["CHK", "CK", "NRV"]:
        return ValveCategory.CHECK

    # 릴리프 밸브
    if valve_type_upper in ["RV", "PRV"]:
        return ValveCategory.RELIEF

    return ValveCategory.UNKNOWN


@router.post("/{session_id}/valve/detect", response_model=ValveDetectionResponse)
async def detect_valves(
    session_id: str,
    rule_id: str = Query(default="valve_detection_default", description="추출 규칙 ID"),
    profile: str = Query(default="default", description="검출 프로필 (default, bwms, chemical 등)"),
    language: str = Query(default="en", description="OCR 언어")
):
    """
    P&ID 밸브 검출

    P&ID 이미지에서 밸브 태그를 추출합니다.
    프로필에 따라 다른 검출 규칙이 적용됩니다.
    """
    start_time = time.time()
    session_service = get_session_service()

    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    file_path = session.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "image/png")}
                data = {"rule_id": rule_id, "language": language}

                response = await client.post(
                    f"{PID_ANALYZER_URL}/api/v1/valve-signal/extract",
                    files=files,
                    data=data
                )

        if response.status_code != 200:
            logger.error(f"PID Analyzer error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Valve detection failed: {response.text}"
            )

        result = response.json()
        extracted_items = result.get("data", {}).get("all_extracted_items", [])

        valves = []
        category_counts = {cat.value: 0 for cat in ValveCategory}

        for idx, item in enumerate(extracted_items):
            valve_id = item.get("id") or item.get("matched_text") or item.get("text", "")
            valve_type = valve_id.split("-")[0] if "-" in valve_id else "Unknown"
            category = _classify_valve_category(valve_id, valve_type)
            category_counts[category.value] += 1

            raw_bbox = item.get("bbox")
            converted_bbox = None
            if raw_bbox:
                try:
                    if isinstance(raw_bbox[0], (list, tuple)):
                        xs = [p[0] for p in raw_bbox]
                        ys = [p[1] for p in raw_bbox]
                        converted_bbox = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
                    else:
                        converted_bbox = [float(v) for v in raw_bbox[:4]]
                except Exception:
                    converted_bbox = None

            valve = ValveItem(
                id=f"valve_{session_id[:8]}_{idx}",
                valve_id=valve_id,
                valve_type=valve_type,
                category=category,
                region_name=item.get("region_name", ""),
                confidence=item.get("confidence", 0.0),
                bbox=converted_bbox,
                verification_status=VerificationStatus.PENDING
            )
            valves.append(valve)

        session_service.update_session(session_id, {
            "pid_valves": [v.model_dump() for v in valves],
            "pid_valve_count": len(valves)
        })

        processing_time = time.time() - start_time

        return ValveDetectionResponse(
            session_id=session_id,
            valves=valves,
            total_count=len(valves),
            categories=category_counts,
            processing_time=round(processing_time, 3),
            regions_detected=result.get("data", {}).get("line_detector", {}).get("total_regions", 0)
        )

    except httpx.RequestError as e:
        logger.error(f"PID Analyzer connection error: {e}")
        raise HTTPException(status_code=503, detail=f"PID Analyzer 서비스 연결 실패: {e}")
