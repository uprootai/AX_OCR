"""Mid-term Roadmap Router - 중기 로드맵 기능 API

- 용접 기호 파싱 (Welding Symbols)
- 표면 거칠기 파싱 (Surface Roughness)
- 수량 추출 (Quantity Extraction)
- 벌룬 매칭 (Balloon Matching)
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging
import time
import uuid
import re
import math

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Mid-term Features"])

# 서비스 주입
_session_service = None


def set_session_service(session_service):
    """세션 서비스 설정"""
    global _session_service
    _session_service = session_service


def get_session_service():
    if _session_service is None:
        raise HTTPException(status_code=500, detail="Session service not initialized")
    return _session_service


# ============================================================
# 용접 기호 파싱 (Welding Symbol Parsing)
# ============================================================

@router.post("/welding-symbols/{session_id}/parse")
async def parse_welding_symbols(session_id: str) -> Dict[str, Any]:
    """
    용접 기호 파싱

    - 도면에서 용접 기호 검출
    - 용접 타입, 크기, 깊이 등 파싱
    - ISO 2553 표준 기반
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # TODO: 실제 용접 기호 검출 로직 (YOLO 학습 필요)
    # 현재는 더미 데이터 반환
    welding_symbols = []

    # 검출된 심볼에서 용접 기호 찾기 (데모용)
    detections = session.get("detections", [])
    for det in detections:
        class_name = det.get("class_name", "").lower()
        if "weld" in class_name or "용접" in class_name:
            welding_symbols.append({
                "id": str(uuid.uuid4()),
                "welding_type": "fillet",
                "location": "arrow_side",
                "size": None,
                "length": None,
                "field_weld": False,
                "all_around": False,
                "bbox": det.get("bbox"),
                "confidence": det.get("confidence", 0.0),
                "raw_text": det.get("class_name"),
            })

    processing_time = (time.time() - start_time) * 1000

    result = {
        "session_id": session_id,
        "welding_symbols": welding_symbols,
        "total_count": len(welding_symbols),
        "by_type": {},
        "processing_time_ms": processing_time,
    }

    # 세션에 저장
    session_service.update_session(session_id, {"welding_symbols": result})

    return result


@router.get("/welding-symbols/{session_id}")
async def get_welding_symbols(session_id: str) -> Dict[str, Any]:
    """용접 기호 파싱 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("welding_symbols")
    if not result:
        return {
            "session_id": session_id,
            "welding_symbols": [],
            "total_count": 0,
            "message": "용접 기호 파싱을 먼저 실행하세요.",
        }

    return result


@router.put("/welding-symbols/{session_id}/{symbol_id}")
async def update_welding_symbol(
    session_id: str,
    symbol_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """용접 기호 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("welding_symbols", {})
    symbols = result.get("welding_symbols", [])

    updated_symbol = None
    for i, sym in enumerate(symbols):
        if sym.get("id") == symbol_id:
            symbols[i] = {**sym, **update}
            updated_symbol = symbols[i]
            break

    result["welding_symbols"] = symbols
    session_service.update_session(session_id, {"welding_symbols": result})

    return {"success": True, "symbol": updated_symbol}


# ============================================================
# 표면 거칠기 파싱 (Surface Roughness Parsing)
# ============================================================

@router.post("/surface-roughness/{session_id}/parse")
async def parse_surface_roughness(session_id: str) -> Dict[str, Any]:
    """
    표면 거칠기 기호 파싱

    - Ra, Rz, Rmax 값 추출
    - 가공 방법 및 방향 인식
    - ISO 1302 표준 기반
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    roughness_symbols = []

    # 치수 텍스트에서 거칠기 값 찾기
    dimensions = session.get("dimensions", [])
    roughness_pattern = re.compile(r'(Ra|Rz|Rmax)\s*(\d+\.?\d*)', re.IGNORECASE)

    for dim in dimensions:
        text = dim.get("text", "") or dim.get("value", "")
        matches = roughness_pattern.findall(str(text))
        for match in matches:
            roughness_type, value = match
            roughness_symbols.append({
                "id": str(uuid.uuid4()),
                "roughness_type": roughness_type.capitalize(),
                "value": float(value),
                "unit": "μm",
                "machining_method": "unknown",
                "lay_direction": "unknown",
                "bbox": dim.get("bbox"),
                "confidence": 0.8,
                "raw_text": f"{roughness_type} {value}",
            })

    processing_time = (time.time() - start_time) * 1000

    # 타입별 집계
    by_type = {}
    for sym in roughness_symbols:
        rt = sym.get("roughness_type", "unknown")
        by_type[rt] = by_type.get(rt, 0) + 1

    result = {
        "session_id": session_id,
        "roughness_symbols": roughness_symbols,
        "total_count": len(roughness_symbols),
        "by_type": by_type,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"surface_roughness": result})

    return result


@router.get("/surface-roughness/{session_id}")
async def get_surface_roughness(session_id: str) -> Dict[str, Any]:
    """표면 거칠기 파싱 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("surface_roughness")
    if not result:
        return {
            "session_id": session_id,
            "roughness_symbols": [],
            "total_count": 0,
            "message": "표면 거칠기 파싱을 먼저 실행하세요.",
        }

    return result


@router.put("/surface-roughness/{session_id}/{symbol_id}")
async def update_surface_roughness(
    session_id: str,
    symbol_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """표면 거칠기 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("surface_roughness", {})
    symbols = result.get("roughness_symbols", [])

    updated_symbol = None
    for i, sym in enumerate(symbols):
        if sym.get("id") == symbol_id:
            symbols[i] = {**sym, **update}
            updated_symbol = symbols[i]
            break

    result["roughness_symbols"] = symbols
    session_service.update_session(session_id, {"surface_roughness": result})

    return {"success": True, "symbol": updated_symbol}


# ============================================================
# 수량 추출 (Quantity Extraction)
# ============================================================

@router.post("/quantity/{session_id}/extract")
async def extract_quantities(session_id: str) -> Dict[str, Any]:
    """
    수량 정보 추출

    - QTY, 수량, EA, SET 등 패턴 인식
    - 벌룬 옆, 테이블, 노트에서 추출
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    quantities = []

    # 수량 패턴 정의
    patterns = [
        (r'QTY[:\s]*(\d+)', 'inline'),
        (r'수량[:\s]*(\d+)', 'inline'),
        (r'(\d+)\s*EA', 'inline'),
        (r'(\d+)\s*SET', 'inline'),
        (r'(\d+)\s*OFF', 'inline'),
        (r"REQ'?D[:\s]*(\d+)", 'inline'),
        (r'×(\d+)', 'balloon'),
        (r'\((\d+)\)', 'balloon'),
    ]

    # 치수에서 수량 찾기
    dimensions = session.get("dimensions", [])
    for dim in dimensions:
        text = str(dim.get("text", "") or dim.get("value", ""))
        for pattern, source in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                qty = int(match) if match.isdigit() else int(match)
                if 1 <= qty <= 1000:  # 합리적인 수량 범위
                    quantities.append({
                        "id": str(uuid.uuid4()),
                        "quantity": qty,
                        "unit": "EA",
                        "source": source,
                        "pattern_matched": pattern,
                        "bbox": dim.get("bbox"),
                        "confidence": 0.85,
                        "raw_text": text,
                    })

    # 검출 결과에서도 찾기
    detections = session.get("detections", [])
    for det in detections:
        class_name = str(det.get("class_name", ""))
        for pattern, source in patterns:
            matches = re.findall(pattern, class_name, re.IGNORECASE)
            for match in matches:
                qty = int(match)
                if 1 <= qty <= 1000:
                    quantities.append({
                        "id": str(uuid.uuid4()),
                        "quantity": qty,
                        "unit": "EA",
                        "source": source,
                        "pattern_matched": pattern,
                        "bbox": det.get("bbox"),
                        "confidence": det.get("confidence", 0.5),
                        "raw_text": class_name,
                    })

    processing_time = (time.time() - start_time) * 1000

    # 출처별 집계
    by_source = {}
    total_quantity = 0
    for q in quantities:
        src = q.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        total_quantity += q.get("quantity", 0)

    result = {
        "session_id": session_id,
        "quantities": quantities,
        "total_items": len(quantities),
        "total_quantity": total_quantity,
        "by_source": by_source,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"quantities": result})

    return result


@router.get("/quantity/{session_id}")
async def get_quantities(session_id: str) -> Dict[str, Any]:
    """수량 추출 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("quantities")
    if not result:
        return {
            "session_id": session_id,
            "quantities": [],
            "total_items": 0,
            "message": "수량 추출을 먼저 실행하세요.",
        }

    return result


@router.put("/quantity/{session_id}/{quantity_id}")
async def update_quantity(
    session_id: str,
    quantity_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """수량 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("quantities", {})
    quantities = result.get("quantities", [])

    updated_item = None
    for i, q in enumerate(quantities):
        if q.get("id") == quantity_id:
            quantities[i] = {**q, **update}
            updated_item = quantities[i]
            break

    result["quantities"] = quantities
    session_service.update_session(session_id, {"quantities": result})

    return {"success": True, "quantity": updated_item}


# ============================================================
# 벌룬 번호 매칭 (Balloon Matching)
# ============================================================

@router.post("/balloon/{session_id}/match")
async def match_balloons(session_id: str) -> Dict[str, Any]:
    """
    벌룬 번호 매칭

    - 벌룬 검출 및 번호 OCR
    - 지시선 추적하여 심볼 연결
    - BOM 테이블과 매칭
    """
    start_time = time.time()

    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    balloons = []

    # 검출 결과에서 벌룬 찾기
    detections = session.get("detections", [])
    balloon_detections = []
    other_detections = []

    for det in detections:
        class_name = str(det.get("class_name", "")).lower()
        if "balloon" in class_name or "번호" in class_name or "item" in class_name:
            balloon_detections.append(det)
        else:
            other_detections.append(det)

    # 벌룬 번호 추출 및 심볼 매칭
    for det in balloon_detections:
        bbox = det.get("bbox", [0, 0, 0, 0])
        center_x = (bbox[0] + bbox[2]) / 2 if len(bbox) >= 4 else 0
        center_y = (bbox[1] + bbox[3]) / 2 if len(bbox) >= 4 else 0

        # 벌룬 번호 추출 (클래스명에서 숫자 추출)
        class_name = det.get("class_name", "")
        numbers = re.findall(r'\d+', class_name)
        balloon_number = numbers[0] if numbers else "?"

        # 가장 가까운 심볼 찾기
        matched_symbol_id = None
        matched_symbol_class = None
        min_distance = float('inf')

        for other in other_detections:
            other_bbox = other.get("bbox", [0, 0, 0, 0])
            if len(other_bbox) >= 4:
                other_center_x = (other_bbox[0] + other_bbox[2]) / 2
                other_center_y = (other_bbox[1] + other_bbox[3]) / 2
                distance = math.sqrt((center_x - other_center_x)**2 + (center_y - other_center_y)**2)
                if distance < min_distance and distance < 500:  # 500px 이내
                    min_distance = distance
                    matched_symbol_id = other.get("id")
                    matched_symbol_class = other.get("class_name")

        balloons.append({
            "id": str(uuid.uuid4()),
            "number": balloon_number,
            "numeric_value": int(balloon_number) if balloon_number.isdigit() else None,
            "shape": "circle",
            "matched_symbol_id": matched_symbol_id,
            "matched_symbol_class": matched_symbol_class,
            "leader_line_endpoint": None,
            "bom_item": None,
            "center": [center_x, center_y],
            "bbox": bbox,
            "confidence": det.get("confidence", 0.0),
        })

    processing_time = (time.time() - start_time) * 1000

    matched_count = sum(1 for b in balloons if b.get("matched_symbol_id"))

    result = {
        "session_id": session_id,
        "balloons": balloons,
        "total_balloons": len(balloons),
        "matched_count": matched_count,
        "unmatched_count": len(balloons) - matched_count,
        "match_rate": (matched_count / len(balloons) * 100) if balloons else 0,
        "processing_time_ms": processing_time,
    }

    session_service.update_session(session_id, {"balloon_matching": result})

    return result


@router.get("/balloon/{session_id}")
async def get_balloons(session_id: str) -> Dict[str, Any]:
    """벌룬 매칭 결과 조회"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("balloon_matching")
    if not result:
        return {
            "session_id": session_id,
            "balloons": [],
            "total_balloons": 0,
            "message": "벌룬 매칭을 먼저 실행하세요.",
        }

    return result


@router.put("/balloon/{session_id}/{balloon_id}")
async def update_balloon(
    session_id: str,
    balloon_id: str,
    update: Dict[str, Any]
) -> Dict[str, Any]:
    """벌룬 매칭 정보 수정"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("balloon_matching", {})
    balloons = result.get("balloons", [])

    updated_balloon = None
    for i, b in enumerate(balloons):
        if b.get("id") == balloon_id:
            balloons[i] = {**b, **update}
            updated_balloon = balloons[i]
            break

    result["balloons"] = balloons
    session_service.update_session(session_id, {"balloon_matching": result})

    return {"success": True, "balloon": updated_balloon}


@router.post("/balloon/{session_id}/{balloon_id}/link")
async def link_balloon_to_symbol(
    session_id: str,
    balloon_id: str,
    symbol_id: str
) -> Dict[str, Any]:
    """벌룬을 심볼에 수동 연결"""
    session_service = get_session_service()
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = session.get("balloon_matching", {})
    balloons = result.get("balloons", [])

    # 심볼 정보 가져오기
    detections = session.get("detections", [])
    symbol_class = None
    for det in detections:
        if det.get("id") == symbol_id:
            symbol_class = det.get("class_name")
            break

    updated_balloon = None
    for i, b in enumerate(balloons):
        if b.get("id") == balloon_id:
            balloons[i]["matched_symbol_id"] = symbol_id
            balloons[i]["matched_symbol_class"] = symbol_class
            updated_balloon = balloons[i]
            break

    # 매칭 통계 업데이트
    matched_count = sum(1 for b in balloons if b.get("matched_symbol_id"))
    result["balloons"] = balloons
    result["matched_count"] = matched_count
    result["unmatched_count"] = len(balloons) - matched_count
    result["match_rate"] = (matched_count / len(balloons) * 100) if balloons else 0

    session_service.update_session(session_id, {"balloon_matching": result})

    return {"success": True, "balloon": updated_balloon}
