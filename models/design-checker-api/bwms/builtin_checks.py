"""
BWMS Built-in Rule Checks
내장 규칙 검사 함수들 (BWMS-001 ~ BWMS-009)
"""
import re
import math
import logging
from typing import List, Dict, Any, Optional

from .base import (
    BWMSEquipment,
    BWMSEquipmentType,
    BWMSViolation,
    BWMS_VALVE_PATTERNS,
)
from .rules_config import BWMS_DESIGN_RULES

logger = logging.getLogger(__name__)


def check_bwms_001_g2_sampling_port(
    equipment_map: Dict[str, BWMSEquipment],
    symbols: List[Dict],
    texts: Optional[List[Dict]] = None
) -> List[BWMSViolation]:
    """BWMS-001: G-2 Sampling Port가 상류(upstream)에 위치하는지 검증

    P&ID에서 G-2 Sampling Port는 ECU 전단(upstream)에 위치해야 합니다.
    G-2는 처리 전 선박평형수 샘플을 채취하는 포트입니다.
    """
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-001"]

    # ECU 찾기
    ecu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.ECU]

    if not ecu_list:
        logger.debug("ECU not found, skipping BWMS-001 check")
        return violations

    # G-2 Sampling Port 텍스트 찾기
    g2_ports = []

    # 심볼에서 찾기
    for symbol in symbols:
        label = str(symbol.get("label", "") or symbol.get("text", "")).upper()
        if "G-2" in label or "G2" in label or "SAMPLING" in label:
            center = symbol.get("center", [0, 0])
            g2_ports.append({
                "id": symbol.get("id", "G2"),
                "x": symbol.get("x", center[0] if isinstance(center, list) else 0),
                "y": symbol.get("y", center[1] if isinstance(center, list) else 0),
                "label": label
            })

    # OCR 텍스트에서 찾기
    if texts:
        for text in texts:
            text_content = str(text.get("text", "")).upper()
            if "G-2" in text_content or ("SAMPLING" in text_content and "PORT" in text_content):
                bbox = text.get("bbox", [[0, 0], [0, 0], [0, 0], [0, 0]])
                if bbox and len(bbox) >= 4:
                    x = (bbox[0][0] + bbox[2][0]) / 2
                    y = (bbox[0][1] + bbox[2][1]) / 2
                else:
                    x, y = 0, 0
                g2_ports.append({
                    "id": f"G2_ocr_{len(g2_ports)}",
                    "x": x,
                    "y": y,
                    "label": text_content
                })

    if not g2_ports:
        logger.debug("G-2 Sampling Port not found, skipping BWMS-001 check")
        return violations

    # 각 G-2가 ECU 전단(upstream = 왼쪽)에 있는지 확인
    for ecu in ecu_list:
        for g2 in g2_ports:
            # G-2가 ECU 오른쪽에 있으면 위반
            if g2["x"] > ecu.x:
                violations.append(BWMSViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    description=rule["description"],
                    severity=rule["severity"],
                    standard=rule["standard"],
                    location={"x": g2["x"], "y": g2["y"]},
                    affected_elements=[g2["id"], ecu.id],
                    suggestion=f"G-2 Sampling Port '{g2['label']}'를 ECU '{ecu.label}' 전단(upstream)으로 이동하세요."
                ))

    return violations


def check_bwms_004_fmu_ecu_sequence(
    equipment_map: Dict[str, BWMSEquipment]
) -> List[BWMSViolation]:
    """BWMS-004: FMU가 ECU 후단에 위치하는지 검증"""
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-004"]

    # FMU와 ECU 장비 찾기
    fmu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.FMU]
    ecu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.ECU]

    if not fmu_list or not ecu_list:
        logger.debug("FMU or ECU not found, skipping BWMS-004 check")
        return violations

    for fmu in fmu_list:
        # FMU의 upstream에 ECU가 있어야 함
        has_ecu_upstream = False

        for upstream_id in fmu.upstream:
            if upstream_id in equipment_map:
                upstream_eq = equipment_map[upstream_id]
                if upstream_eq.equipment_type == BWMSEquipmentType.ECU:
                    has_ecu_upstream = True
                    break

        # 연결 정보가 없는 경우 위치 기반 검사 (X 좌표 비교)
        if not fmu.upstream:
            for ecu in ecu_list:
                # FMU가 ECU 오른쪽(downstream)에 있어야 함
                if fmu.x > ecu.x:
                    has_ecu_upstream = True
                    break

        if not has_ecu_upstream:
            violations.append(BWMSViolation(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_name_en=rule["name_en"],
                description=rule["description"],
                severity=rule["severity"],
                standard=rule["standard"],
                location={"x": fmu.x, "y": fmu.y},
                affected_elements=[fmu.id],
                suggestion=f"FMU '{fmu.label}'를 ECU 후단(downstream)에 배치하세요."
            ))

    return violations


def check_bwms_005_gds_position(
    equipment_map: Dict[str, BWMSEquipment]
) -> List[BWMSViolation]:
    """BWMS-005: GDS가 ECU/HGU 상부에 위치하는지 검증"""
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-005"]

    # GDS, ECU, HGU 장비 찾기
    gds_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.GDS]
    ecu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.ECU]
    hgu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.HGU]

    reference_units = ecu_list + hgu_list

    if not gds_list or not reference_units:
        logger.debug("GDS or ECU/HGU not found, skipping BWMS-005 check")
        return violations

    for gds in gds_list:
        is_above_reference = False

        for ref_unit in reference_units:
            # GDS의 Y 좌표가 ECU/HGU보다 작아야 함 (이미지 좌표계에서 위쪽)
            # 그리고 X 좌표가 비슷해야 함 (같은 수직선상)
            x_tolerance = 200  # 픽셀
            if abs(gds.x - ref_unit.x) < x_tolerance and gds.y < ref_unit.y:
                is_above_reference = True
                break

        if not is_above_reference and reference_units:
            violations.append(BWMSViolation(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_name_en=rule["name_en"],
                description=rule["description"],
                severity=rule["severity"],
                standard=rule["standard"],
                location={"x": gds.x, "y": gds.y},
                affected_elements=[gds.id],
                suggestion=f"GDS '{gds.label}'를 ECU 또는 HGU 상부에 배치하세요."
            ))

    return violations


def check_bwms_006_tsu_apu_distance(
    equipment_map: Dict[str, BWMSEquipment],
    scale_factor: float = 1.0  # 픽셀당 미터 (기본값: 스케일 없음)
) -> List[BWMSViolation]:
    """BWMS-006: TSU와 APU 간 거리가 5m 이내인지 검증

    TRO Sensor Unit(TSU)과 Air Pump Unit(APU)은 가까이 배치되어야 합니다.
    스케일 정보가 없으면 픽셀 기준 거리로 경고 (추정치).
    """
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-006"]

    # TSU, APU 찾기
    tsu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.TSU]
    apu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.APU]

    if not tsu_list or not apu_list:
        logger.debug("TSU or APU not found, skipping BWMS-006 check")
        return violations

    # 5m 제한 (스케일이 없으면 픽셀 기준 500px를 대략 5m로 가정)
    max_distance_m = 5.0
    max_distance_px = 500 if scale_factor == 1.0 else max_distance_m / scale_factor

    for tsu in tsu_list:
        for apu in apu_list:
            distance_px = math.sqrt((tsu.x - apu.x)**2 + (tsu.y - apu.y)**2)

            if distance_px > max_distance_px:
                distance_m = distance_px * scale_factor if scale_factor != 1.0 else distance_px / 100
                violations.append(BWMSViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    description=rule["description"],
                    severity=rule["severity"],
                    standard=rule["standard"],
                    location={"x": (tsu.x + apu.x) / 2, "y": (tsu.y + apu.y) / 2},
                    affected_elements=[tsu.id, apu.id],
                    suggestion=f"TSU '{tsu.label}'와 APU '{apu.label}' 거리가 {distance_m:.1f}m로 추정됩니다. 5m 이내로 배치하세요. (스케일 정보 필요)"
                ))

    return violations


def check_bwms_007_mixing_pump_capacity(
    equipment_map: Dict[str, BWMSEquipment],
    symbols: List[Dict],
    texts: Optional[List[Dict]] = None
) -> List[BWMSViolation]:
    """BWMS-007: Mixing Pump 용량이 Ballast Pump의 4.3%인지 검증

    Mixing Pump의 용량(m3/h)이 Ballast Pump의 4.3%와 일치해야 합니다.
    OCR 텍스트에서 용량 정보를 추출하여 비교합니다.
    """
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-007"]

    # Pump 관련 텍스트에서 용량 추출
    pump_specs = {}  # {"pump_name": capacity_m3h}

    # 용량 패턴: 숫자 m3/h 또는 숫자 m3/h
    capacity_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m[3]/h|m3/h|CMH)", re.IGNORECASE)

    if texts:
        for text in texts:
            text_content = str(text.get("text", "")).upper()

            # Mixing Pump 또는 Ballast Pump 텍스트 찾기
            is_mixing = "MIXING" in text_content and "PUMP" in text_content
            is_ballast = "BALLAST" in text_content and "PUMP" in text_content

            if is_mixing or is_ballast:
                match = capacity_pattern.search(text_content)
                if match:
                    capacity = float(match.group(1))
                    pump_type = "mixing_pump" if is_mixing else "ballast_pump"
                    pump_specs[pump_type] = capacity

    # 심볼 라벨에서도 검색
    for symbol in symbols:
        label = str(symbol.get("label", "")).upper()
        if "PUMP" in label:
            is_mixing = "MIXING" in label or "MIX" in label
            is_ballast = "BALLAST" in label or "BL" in label

            if is_mixing or is_ballast:
                match = capacity_pattern.search(label)
                if match:
                    capacity = float(match.group(1))
                    pump_type = "mixing_pump" if is_mixing else "ballast_pump"
                    if pump_type not in pump_specs:
                        pump_specs[pump_type] = capacity

    # 두 펌프 모두 있어야 비교 가능
    if "mixing_pump" not in pump_specs or "ballast_pump" not in pump_specs:
        logger.debug("Mixing Pump or Ballast Pump capacity not found in OCR, skipping BWMS-007 check")
        return violations

    mixing_capacity = pump_specs["mixing_pump"]
    ballast_capacity = pump_specs["ballast_pump"]
    expected_mixing = ballast_capacity * 0.043  # 4.3%

    # 허용 오차 +/-10%
    tolerance = 0.1
    if abs(mixing_capacity - expected_mixing) / expected_mixing > tolerance:
        violations.append(BWMSViolation(
            rule_id=rule["id"],
            rule_name=rule["name"],
            rule_name_en=rule["name_en"],
            description=rule["description"],
            severity=rule["severity"],
            standard=rule["standard"],
            location={"x": 0, "y": 0},
            affected_elements=["Mixing Pump", "Ballast Pump"],
            suggestion=f"Mixing Pump 용량({mixing_capacity}m3/h)이 Ballast Pump({ballast_capacity}m3/h)의 4.3%({expected_mixing:.1f}m3/h)와 일치하지 않습니다."
        ))

    return violations


def check_bwms_008_ecs_valve_position(
    equipment_map: Dict[str, BWMSEquipment],
    symbols: List[Dict],
    valve_patterns: List[str] = None
) -> List[BWMSViolation]:
    """BWMS-008: ECS 밸브 위치 검증"""
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-008"]

    if valve_patterns is None:
        valve_patterns = BWMS_VALVE_PATTERNS

    # ECS 관련 장비 (ECU, FMU, TSU 등)
    ecs_equipment = [
        eq for eq in equipment_map.values()
        if eq.equipment_type in [
            BWMSEquipmentType.ECU, BWMSEquipmentType.FMU,
            BWMSEquipmentType.TSU, BWMSEquipmentType.ANU
        ]
    ]

    if not ecs_equipment:
        return violations

    # ECS 영역의 bounding box 계산
    ecs_x_min = min(eq.x for eq in ecs_equipment)
    ecs_x_max = max(eq.x + eq.width for eq in ecs_equipment)
    ecs_y_min = min(eq.y for eq in ecs_equipment)
    ecs_y_max = max(eq.y + eq.height for eq in ecs_equipment)

    # 밸브 심볼 찾기
    for symbol in symbols:
        symbol_type = str(symbol.get("type", "") or symbol.get("class", "")).lower()
        tag = str(symbol.get("tag_number", "") or symbol.get("tag", "") or "")

        # BWMS 밸브인지 확인
        is_bwms_valve = False
        for pattern in valve_patterns:
            if re.search(pattern, tag, re.IGNORECASE):
                is_bwms_valve = True
                break

        if is_bwms_valve or "valve" in symbol_type:
            valve_x = symbol.get("x", 0)
            valve_y = symbol.get("y", 0)

            # ECS 영역 근처에 있어야 함 (확장된 영역 검사)
            margin = 300  # 픽셀
            is_near_ecs = (
                ecs_x_min - margin <= valve_x <= ecs_x_max + margin and
                ecs_y_min - margin <= valve_y <= ecs_y_max + margin
            )

            # BWMS 밸브가 ECS 영역에서 너무 멀리 떨어져 있으면 경고
            if is_bwms_valve and not is_near_ecs:
                violations.append(BWMSViolation(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_name_en=rule["name_en"],
                    description=f"밸브 '{tag}'가 ECS 장비 영역에서 떨어져 있습니다",
                    severity=rule["severity"],
                    standard=rule["standard"],
                    location={"x": valve_x, "y": valve_y},
                    affected_elements=[str(symbol.get("id", ""))],
                    suggestion=f"밸브 '{tag}'를 ECS 장비 근처에 배치하세요."
                ))

    return violations


def check_bwms_009_hychlor_filter(
    equipment_map: Dict[str, BWMSEquipment],
    symbols: List[Dict]
) -> List[BWMSViolation]:
    """BWMS-009: HYCHLOR 필터가 HGU 전단에 위치하는지 검증"""
    violations = []
    rule = BWMS_DESIGN_RULES["BWMS-009"]

    # HGU 장비 찾기
    hgu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.HGU]

    if not hgu_list:
        logger.debug("HGU not found, skipping BWMS-009 check")
        return violations

    # 필터 심볼 찾기
    filters = []
    for symbol in symbols:
        symbol_type = str(symbol.get("type", "") or symbol.get("class", "")).lower()
        label = str(symbol.get("label", "")).lower()

        if "filter" in symbol_type or "filter" in label or "strainer" in symbol_type:
            filters.append({
                "id": str(symbol.get("id", "")),
                "x": symbol.get("x", 0),
                "y": symbol.get("y", 0),
                "label": symbol.get("label", "Filter")
            })

    # 각 HGU에 대해 전단에 필터가 있는지 확인
    for hgu in hgu_list:
        has_upstream_filter = False

        for flt in filters:
            # 필터가 HGU 왼쪽(upstream)에 있어야 함
            # 그리고 Y 좌표가 비슷해야 함 (같은 수평선상)
            y_tolerance = 150  # 픽셀
            if flt["x"] < hgu.x and abs(flt["y"] - hgu.y) < y_tolerance:
                has_upstream_filter = True
                break

        if not has_upstream_filter and filters:
            # 필터가 있지만 HGU 전단에 없는 경우
            violations.append(BWMSViolation(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_name_en=rule["name_en"],
                description=rule["description"],
                severity=rule["severity"],
                standard=rule["standard"],
                location={"x": hgu.x, "y": hgu.y},
                affected_elements=[hgu.id],
                suggestion=f"HGU '{hgu.label}' 전단(upstream)에 필터를 배치하세요."
            ))

    return violations
