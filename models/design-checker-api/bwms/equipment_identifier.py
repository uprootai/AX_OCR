"""
BWMS Equipment Identifier
심볼 및 텍스트에서 BWMS 장비 식별 및 연결 그래프 구축
"""
import logging
from typing import List, Dict, Any, Optional

from .base import (
    BWMSEquipment,
    BWMSEquipmentType,
    BWMS_EQUIPMENT_PATTERNS,
    match_equipment_type,
    get_center,
    is_near,
)

logger = logging.getLogger(__name__)


def identify_bwms_equipment(
    symbols: List[Dict],
    texts: Optional[List[Dict]] = None,
    equipment_patterns: Dict[BWMSEquipmentType, List[str]] = None
) -> List[BWMSEquipment]:
    """심볼과 텍스트에서 BWMS 장비 식별

    Args:
        symbols: 검출된 심볼 목록
        texts: OCR로 추출된 텍스트 목록 (optional)
        equipment_patterns: 장비 패턴 딕셔너리 (optional, 기본값 사용)

    Returns:
        식별된 BWMS 장비 목록
    """
    if equipment_patterns is None:
        equipment_patterns = BWMS_EQUIPMENT_PATTERNS

    equipment_list = []

    # 1. 심볼의 라벨/태그에서 BWMS 장비 식별
    for symbol in symbols:
        symbol_id = str(symbol.get("id", ""))
        label = str(symbol.get("label", "") or symbol.get("class", "") or "")
        tag = str(symbol.get("tag_number", "") or symbol.get("tag", "") or "")

        # 라벨 또는 태그에서 BWMS 장비 타입 매칭
        eq_type = (
            match_equipment_type(label, equipment_patterns) or
            match_equipment_type(tag, equipment_patterns)
        )

        if eq_type:
            equipment = BWMSEquipment(
                id=symbol_id,
                equipment_type=eq_type,
                label=label or tag,
                x=symbol.get("x", 0),
                y=symbol.get("y", 0),
                width=symbol.get("width", 0),
                height=symbol.get("height", 0),
                bbox=symbol.get("bbox", [])
            )
            equipment_list.append(equipment)

    # 2. OCR 텍스트에서 추가 BWMS 장비 식별
    if texts:
        for text_item in texts:
            text = str(text_item.get("text", ""))
            eq_type = match_equipment_type(text, equipment_patterns)

            if eq_type:
                # 이미 식별된 장비인지 확인 (위치 기반)
                bbox = text_item.get("bbox", text_item.get("bounding_box", []))
                center = get_center(bbox)

                # 중복 체크
                is_duplicate = False
                for eq in equipment_list:
                    if is_near(center, (eq.x, eq.y), threshold=100):
                        is_duplicate = True
                        break

                if not is_duplicate and center:
                    equipment = BWMSEquipment(
                        id=f"text_{len(equipment_list)}",
                        equipment_type=eq_type,
                        label=text,
                        x=center[0],
                        y=center[1],
                        bbox=bbox if isinstance(bbox, list) else []
                    )
                    equipment_list.append(equipment)

    logger.info(f"Identified {len(equipment_list)} BWMS equipment")
    return equipment_list


def build_flow_graph(
    equipment_list: List[BWMSEquipment],
    connections: List[Dict],
    lines: Optional[List[Dict]] = None
) -> Dict[str, BWMSEquipment]:
    """장비 연결 그래프 구축 (upstream/downstream 분석)

    Args:
        equipment_list: BWMS 장비 목록
        connections: 연결 정보 목록
        lines: 라인 정보 목록 (optional, 향후 확장용)

    Returns:
        장비 ID로 인덱싱된 장비 맵
    """
    # 장비 ID로 인덱싱
    equipment_map = {eq.id: eq for eq in equipment_list}

    # 연결 정보 처리
    for conn in connections:
        source_id = str(conn.get("source_id", conn.get("from", "")))
        target_id = str(conn.get("target_id", conn.get("to", "")))

        if source_id in equipment_map:
            equipment_map[source_id].downstream.append(target_id)
            equipment_map[source_id].connected_to.append(target_id)

        if target_id in equipment_map:
            equipment_map[target_id].upstream.append(source_id)
            equipment_map[target_id].connected_to.append(source_id)

    return equipment_map
