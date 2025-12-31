"""P&ID Equipment Detection Router

장비 검출 엔드포인트
"""

import os
import time
import logging

from fastapi import APIRouter, HTTPException, Query
import httpx

from schemas.pid_features import (
    EquipmentType,
    EquipmentItem,
    EquipmentDetectionResponse,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["P&ID Equipment"])

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


def _classify_equipment_type(tag: str) -> EquipmentType:
    """장비 타입 분류"""
    tag_upper = tag.upper()

    if any(p in tag_upper for p in ["PUMP", "P-", "PP-"]):
        return EquipmentType.PUMP
    if any(p in tag_upper for p in ["VALVE", "V-", "XV", "SV", "CV"]):
        return EquipmentType.VALVE
    if any(p in tag_upper for p in ["TANK", "T-", "TK"]):
        return EquipmentType.TANK
    if any(p in tag_upper for p in ["HX", "E-", "EXCHANGER"]):
        return EquipmentType.HEAT_EXCHANGER
    if any(p in tag_upper for p in ["COMP", "C-", "K-"]):
        return EquipmentType.COMPRESSOR
    if any(p in tag_upper for p in ["FILTER", "F-", "FLT"]):
        return EquipmentType.FILTER
    if any(p in tag_upper for p in ["CTRL", "PLC", "DCS"]):
        return EquipmentType.CONTROLLER
    if any(p in tag_upper for p in ["PT", "TT", "FT", "LT", "AT"]):
        return EquipmentType.SENSOR

    return EquipmentType.OTHER


@router.post("/{session_id}/equipment/detect", response_model=EquipmentDetectionResponse)
async def detect_equipment(
    session_id: str,
    profile: str = Query(default="default", description="장비 프로필"),
    language: str = Query(default="en", description="OCR 언어")
):
    """
    P&ID 장비 검출

    P&ID 이미지에서 장비 태그를 검출합니다.
    프로필에 따라 특화된 장비 타입을 인식합니다.
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
                data = {"profile_id": profile, "language": language}

                response = await client.post(
                    f"{PID_ANALYZER_URL}/api/v1/equipment/detect",
                    files=files,
                    data=data
                )

        if response.status_code != 200:
            logger.error(f"Equipment detection error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Equipment detection failed: {response.text}"
            )

        result = response.json()
        detected_equipment = result.get("data", {}).get("equipment", [])

        equipment_items = []
        type_counts = {et.value: 0 for et in EquipmentType}
        vendor_supply_count = 0

        for idx, eq in enumerate(detected_equipment):
            tag = eq.get("tag", "")
            eq_type = _classify_equipment_type(tag)
            type_counts[eq_type.value] += 1

            is_vendor_supply = eq.get("vendor_supply", False) or "*" in tag
            if is_vendor_supply:
                vendor_supply_count += 1

            equipment_item = EquipmentItem(
                id=f"eq_{session_id[:8]}_{idx}",
                tag=tag,
                equipment_type=eq_type,
                description=eq.get("description", ""),
                vendor_supply=is_vendor_supply,
                confidence=eq.get("confidence", 0.0),
                bbox=eq.get("bbox"),
                verification_status=VerificationStatus.PENDING
            )
            equipment_items.append(equipment_item)

        session_service.update_session(session_id, {
            "pid_equipment": [eq.model_dump() for eq in equipment_items],
            "pid_equipment_count": len(equipment_items)
        })

        processing_time = time.time() - start_time

        return EquipmentDetectionResponse(
            session_id=session_id,
            equipment=equipment_items,
            total_count=len(equipment_items),
            by_type=type_counts,
            vendor_supply_count=vendor_supply_count,
            processing_time=round(processing_time, 3)
        )

    except httpx.RequestError as e:
        logger.error(f"PID Analyzer connection error: {e}")
        raise HTTPException(status_code=503, detail=f"PID Analyzer 서비스 연결 실패: {e}")
