"""
BWMS (Ballast Water Management System) 설계 규칙
TECHCROSS P&ID 설계 검증용 규칙 모듈

규칙 목록:
- BWMS-001: G-2 Sampling Port 상류(upstream) 위치 확인
- BWMS-004: FMU가 ECU 후단에 위치 확인
- BWMS-005: GDS가 ECU/HGU 상부에 위치 확인
- BWMS-006: TSU-APU 근접 확인 (5m 이내) - 스케일 필요
- BWMS-007: Mixing Pump = Ballast Pump × 4.3% 확인
- BWMS-008: ECS 밸브 위치 확인
- BWMS-009: HYCHLOR 필터 위치 확인
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =====================
# BWMS Equipment Types
# =====================

class BWMSEquipmentType(str, Enum):
    """BWMS 장비 유형"""
    # ECS 시스템
    ECU = "ECU"      # Electrolyzer Cell Unit - 전해조 유닛
    FMU = "FMU"      # Flow Meter Unit - 유량계
    ANU = "ANU"      # Active Neutralization Unit - 자동 중화 장치
    TSU = "TSU"      # TRO Sensor Unit - TRO 센서
    APU = "APU"      # Air Pump Unit - 공기 펌프
    GDS = "GDS"      # Gas Detection Sensor - 가스 감지 센서
    EWU = "EWU"      # EM Washing Unit - 전극 세척 유닛
    CPC = "CPC"      # Control PC - 제어 PC
    PCU = "PCU"      # Pump Control Unit - 펌프 제어 유닛
    TRO = "TRO"      # Total Residual Oxidant - 잔류산화물

    # HYCHLOR 시스템 추가
    HGU = "HGU"      # Hypochlorite Generation Unit - 차아염소산 생성
    DMU = "DMU"      # Degas Module Unit - 탈기 모듈
    NIU = "NIU"      # Neutralization Injection Unit - 중화 주입 유닛
    DTS = "DTS"      # DPD TRO Sensor - DPD TRO 센서

    # 밸브 타입
    VALVE = "VALVE"  # 일반 밸브
    FILTER = "FILTER"  # 필터


# BWMS 장비 패턴 (OCR 텍스트에서 매칭)
BWMS_EQUIPMENT_PATTERNS = {
    BWMSEquipmentType.ECU: [r"ECU[-\s]?\d*", r"ELECTROLYZER", r"ELECTRO[-\s]?CELL"],
    BWMSEquipmentType.FMU: [r"FMU[-\s]?\d*", r"FLOW[-\s]?METER"],
    BWMSEquipmentType.ANU: [r"ANU[-\s]?\d*", r"NEUTRALIZATION"],
    BWMSEquipmentType.TSU: [r"TSU[-\s]?\d*", r"TRO[-\s]?SENSOR"],
    BWMSEquipmentType.APU: [r"APU[-\s]?\d*", r"AIR[-\s]?PUMP"],
    BWMSEquipmentType.GDS: [r"GDS[-\s]?\d*", r"GAS[-\s]?DETECT"],
    BWMSEquipmentType.EWU: [r"EWU[-\s]?\d*", r"WASHING[-\s]?UNIT"],
    BWMSEquipmentType.CPC: [r"CPC[-\s]?\d*", r"CONTROL[-\s]?PC"],
    BWMSEquipmentType.PCU: [r"PCU[-\s]?\d*", r"PUMP[-\s]?CONTROL"],
    BWMSEquipmentType.HGU: [r"HGU[-\s]?\d*", r"HYPOCHLORITE"],
    BWMSEquipmentType.DMU: [r"DMU[-\s]?\d*", r"DEGAS"],
    BWMSEquipmentType.NIU: [r"NIU[-\s]?\d*", r"NEUTRALIZATION[-\s]?INJ"],
    BWMSEquipmentType.DTS: [r"DTS[-\s]?\d*", r"DPD[-\s]?TRO"],
}

# BWMS 밸브 패턴
BWMS_VALVE_PATTERNS = [
    r"BWV[-\s]?\d+",   # Ball Valve for BWMS
    r"BAV[-\s]?\d+",   # Ball Valve
    r"BCV[-\s]?\d+",   # Ball Check Valve
    r"BBV[-\s]?\d+",   # Butterfly Valve
    r"BXV[-\s]?\d+",   # 3-way Valve
    r"BSV[-\s]?\d+",   # Safety Valve
]


# =====================
# Data Classes
# =====================

@dataclass
class BWMSEquipment:
    """BWMS 장비 정보"""
    id: str
    equipment_type: BWMSEquipmentType
    label: str
    x: float
    y: float
    width: float = 0
    height: float = 0
    bbox: List[float] = field(default_factory=list)
    connected_to: List[str] = field(default_factory=list)
    upstream: List[str] = field(default_factory=list)
    downstream: List[str] = field(default_factory=list)


@dataclass
class BWMSViolation:
    """BWMS 규칙 위반 정보"""
    rule_id: str
    rule_name: str
    rule_name_en: str
    description: str
    severity: str  # error, warning, info
    standard: str
    location: Optional[Dict] = None
    affected_elements: List[str] = field(default_factory=list)
    suggestion: str = ""


# =====================
# BWMS Design Rules
# =====================

BWMS_DESIGN_RULES = {
    "BWMS-001": {
        "id": "BWMS-001",
        "name": "G-2 Sampling Port 상류 위치",
        "name_en": "G-2 Sampling Port Upstream Position",
        "description": "G-2 Sampling Port는 상류(upstream)에 위치해야 합니다",
        "category": "position",
        "severity": "warning",
        "standard": "TECHCROSS BWMS Standard"
    },
    "BWMS-004": {
        "id": "BWMS-004",
        "name": "FMU-ECU 순서 검증",
        "name_en": "FMU-ECU Sequence Validation",
        "description": "FMU(유량계)는 ECU(전해조) 후단에 위치해야 합니다",
        "category": "sequence",
        "severity": "error",
        "standard": "TECHCROSS BWMS Standard"
    },
    "BWMS-005": {
        "id": "BWMS-005",
        "name": "GDS 위치 검증",
        "name_en": "GDS Position Validation",
        "description": "GDS(가스감지센서)는 ECU 또는 HGU 상부에 위치해야 합니다",
        "category": "position",
        "severity": "error",
        "standard": "TECHCROSS BWMS Standard"
    },
    "BWMS-006": {
        "id": "BWMS-006",
        "name": "TSU-APU 거리 제한",
        "name_en": "TSU-APU Distance Limit",
        "description": "TSU와 APU 간 거리는 5m 이내여야 합니다",
        "category": "distance",
        "severity": "warning",
        "standard": "TECHCROSS BWMS Standard",
        "requires_scale": True
    },
    "BWMS-007": {
        "id": "BWMS-007",
        "name": "Mixing Pump 용량 검증",
        "name_en": "Mixing Pump Capacity Validation",
        "description": "Mixing Pump 용량은 Ballast Pump의 4.3%여야 합니다",
        "category": "specification",
        "severity": "warning",
        "standard": "TECHCROSS BWMS Standard",
        "requires_ocr": True
    },
    "BWMS-008": {
        "id": "BWMS-008",
        "name": "ECS 밸브 위치 검증",
        "name_en": "ECS Valve Position Validation",
        "description": "ECS 시스템 밸브가 올바른 위치에 배치되어야 합니다",
        "category": "position",
        "severity": "warning",
        "standard": "TECHCROSS BWMS Standard"
    },
    "BWMS-009": {
        "id": "BWMS-009",
        "name": "HYCHLOR 필터 위치 검증",
        "name_en": "HYCHLOR Filter Position Validation",
        "description": "HYCHLOR 시스템 필터가 HGU 전단에 위치해야 합니다",
        "category": "sequence",
        "severity": "warning",
        "standard": "TECHCROSS BWMS Standard"
    },
}


# =====================
# BWMS Checker Class
# =====================

class BWMSChecker:
    """BWMS P&ID 설계 검증기"""

    def __init__(self):
        self.rules = BWMS_DESIGN_RULES
        self.equipment_patterns = BWMS_EQUIPMENT_PATTERNS
        self.valve_patterns = BWMS_VALVE_PATTERNS

    def identify_bwms_equipment(
        self,
        symbols: List[Dict],
        texts: Optional[List[Dict]] = None
    ) -> List[BWMSEquipment]:
        """심볼과 텍스트에서 BWMS 장비 식별"""
        equipment_list = []

        # 1. 심볼의 라벨/태그에서 BWMS 장비 식별
        for symbol in symbols:
            symbol_id = str(symbol.get("id", ""))
            label = str(symbol.get("label", "") or symbol.get("class", "") or "")
            tag = str(symbol.get("tag_number", "") or symbol.get("tag", "") or "")

            # 라벨 또는 태그에서 BWMS 장비 타입 매칭
            eq_type = self._match_equipment_type(label) or self._match_equipment_type(tag)

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
                eq_type = self._match_equipment_type(text)

                if eq_type:
                    # 이미 식별된 장비인지 확인 (위치 기반)
                    bbox = text_item.get("bbox", text_item.get("bounding_box", []))
                    center = self._get_center(bbox)

                    # 중복 체크
                    is_duplicate = False
                    for eq in equipment_list:
                        if self._is_near(center, (eq.x, eq.y), threshold=100):
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

    def _match_equipment_type(self, text: str) -> Optional[BWMSEquipmentType]:
        """텍스트에서 BWMS 장비 타입 매칭"""
        text_upper = text.upper()

        for eq_type, patterns in self.equipment_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    return eq_type

        return None

    def _get_center(self, bbox) -> Optional[Tuple[float, float]]:
        """bbox의 중심점 계산"""
        if not bbox:
            return None

        if isinstance(bbox[0], list):  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형식
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            return (sum(xs) / len(xs), sum(ys) / len(ys))
        elif len(bbox) >= 4:  # [x1, y1, x2, y2] 형식
            return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

        return None

    def _is_near(
        self,
        point1: Optional[Tuple[float, float]],
        point2: Optional[Tuple[float, float]],
        threshold: float = 50
    ) -> bool:
        """두 점이 가까운지 확인"""
        if not point1 or not point2:
            return False

        distance = ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5
        return distance < threshold

    def build_flow_graph(
        self,
        equipment_list: List[BWMSEquipment],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None
    ) -> Dict[str, BWMSEquipment]:
        """장비 연결 그래프 구축 (upstream/downstream 분석)"""
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

    def check_bwms_004_fmu_ecu_sequence(
        self,
        equipment_map: Dict[str, BWMSEquipment]
    ) -> List[BWMSViolation]:
        """BWMS-004: FMU가 ECU 후단에 위치하는지 검증"""
        violations = []
        rule = self.rules["BWMS-004"]

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
        self,
        equipment_map: Dict[str, BWMSEquipment]
    ) -> List[BWMSViolation]:
        """BWMS-005: GDS가 ECU/HGU 상부에 위치하는지 검증"""
        violations = []
        rule = self.rules["BWMS-005"]

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

    def check_bwms_008_ecs_valve_position(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict]
    ) -> List[BWMSViolation]:
        """BWMS-008: ECS 밸브 위치 검증"""
        violations = []
        rule = self.rules["BWMS-008"]

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
            for pattern in self.valve_patterns:
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
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict]
    ) -> List[BWMSViolation]:
        """BWMS-009: HYCHLOR 필터가 HGU 전단에 위치하는지 검증"""
        violations = []
        rule = self.rules["BWMS-009"]

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

    def check_bwms_001_g2_sampling_port(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict],
        texts: Optional[List[Dict]] = None
    ) -> List[BWMSViolation]:
        """BWMS-001: G-2 Sampling Port가 상류(upstream)에 위치하는지 검증

        P&ID에서 G-2 Sampling Port는 ECU 전단(upstream)에 위치해야 합니다.
        G-2는 처리 전 선박평형수 샘플을 채취하는 포트입니다.
        """
        violations = []
        rule = self.rules["BWMS-001"]

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
                g2_ports.append({
                    "id": symbol.get("id", "G2"),
                    "x": symbol.get("x", symbol.get("center", [0, 0])[0] if isinstance(symbol.get("center"), list) else 0),
                    "y": symbol.get("y", symbol.get("center", [0, 0])[1] if isinstance(symbol.get("center"), list) else 0),
                    "label": label
                })

        # OCR 텍스트에서 찾기
        if texts:
            for text in texts:
                text_content = str(text.get("text", "")).upper()
                if "G-2" in text_content or ("SAMPLING" in text_content and "PORT" in text_content):
                    bbox = text.get("bbox", [[0, 0], [0, 0], [0, 0], [0, 0]])
                    # bbox는 4개 점 좌표 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
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
            # G-2 없으면 경고 없이 스킵 (있어야 하는 건 아님)
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

    def check_bwms_006_tsu_apu_distance(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        scale_factor: float = 1.0  # 픽셀당 미터 (기본값: 스케일 없음)
    ) -> List[BWMSViolation]:
        """BWMS-006: TSU와 APU 간 거리가 5m 이내인지 검증

        TRO Sensor Unit(TSU)과 Air Pump Unit(APU)은 가까이 배치되어야 합니다.
        스케일 정보가 없으면 픽셀 기준 거리로 경고 (추정치).
        """
        violations = []
        rule = self.rules["BWMS-006"]

        # TSU, APU 찾기
        tsu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.TSU]
        apu_list = [eq for eq in equipment_map.values() if eq.equipment_type == BWMSEquipmentType.APU]

        if not tsu_list or not apu_list:
            logger.debug("TSU or APU not found, skipping BWMS-006 check")
            return violations

        # 5m 제한 (스케일이 없으면 픽셀 기준 500px를 대략 5m로 가정)
        max_distance_m = 5.0
        max_distance_px = 500 if scale_factor == 1.0 else max_distance_m / scale_factor

        import math
        for tsu in tsu_list:
            for apu in apu_list:
                distance_px = math.sqrt((tsu.x - apu.x)**2 + (tsu.y - apu.y)**2)

                if distance_px > max_distance_px:
                    distance_m = distance_px * scale_factor if scale_factor != 1.0 else distance_px / 100  # 픽셀 기준 추정
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
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict],
        texts: Optional[List[Dict]] = None
    ) -> List[BWMSViolation]:
        """BWMS-007: Mixing Pump 용량이 Ballast Pump의 4.3%인지 검증

        Mixing Pump의 용량(m³/h)이 Ballast Pump의 4.3%와 일치해야 합니다.
        OCR 텍스트에서 용량 정보를 추출하여 비교합니다.
        """
        violations = []
        rule = self.rules["BWMS-007"]

        # Pump 관련 텍스트에서 용량 추출
        pump_specs = {}  # {"pump_name": capacity_m3h}

        # 용량 패턴: 숫자 m³/h 또는 숫자 m3/h
        capacity_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m[³3]/h|m3/h|CMH)", re.IGNORECASE)

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

        # 허용 오차 ±10%
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
                suggestion=f"Mixing Pump 용량({mixing_capacity}m³/h)이 Ballast Pump({ballast_capacity}m³/h)의 4.3%({expected_mixing:.1f}m³/h)와 일치하지 않습니다."
            ))

        return violations

    def _should_apply_rule(self, rule: Dict, equipment_map: Dict[str, Any]) -> bool:
        """규칙이 현재 시스템 타입에 적용되어야 하는지 확인"""
        product_type = rule.get('product_type', 'ALL')
        if product_type == 'ALL':
            return True

        # 시스템 타입 추론 (HGU 있으면 HYCHLOR, 아니면 ECS)
        has_hgu = any(eq.equipment_type.value == 'HGU' for eq in equipment_map.values())
        current_system = 'HYCHLOR' if has_hgu else 'ECS'

        return product_type == current_system

    def _check_dynamic_rules(
        self,
        equipment_map: Dict[str, Any],
        symbols: List[Dict],
        connections: List[Dict],
        lines: Optional[List[Dict]],
        texts: Optional[List[Dict]],
        enabled_rules: List[str]
    ) -> List[BWMSViolation]:
        """동적으로 로드된 규칙 검사 (Excel 업로드)"""
        violations = []

        # _dynamic_rules 속성이 없으면 건너뜀
        if not hasattr(self, '_dynamic_rules') or not self._dynamic_rules:
            logger.debug("No dynamic rules loaded")
            return violations

        logger.info(f"Checking {len(self._dynamic_rules)} dynamic rules")
        for rule_id, rule in self._dynamic_rules.items():
            # product_type 필터링: 현재 시스템에 해당하는 규칙만 적용
            if not self._should_apply_rule(rule, equipment_map):
                logger.debug(f"Skipping rule {rule_id}: product_type mismatch")
                continue

            check_type = rule.get('check_type', 'manual')
            equipment_names = rule.get('equipment', '').split(',') if rule.get('equipment') else []
            condition = rule.get('condition', '')
            condition_value = rule.get('condition_value', '')

            try:
                logger.info(f"Processing dynamic rule: {rule_id} (type={check_type}, equipment={equipment_names})")
                if check_type == 'position':
                    pos_violations = self._check_dynamic_position(
                        rule, equipment_map, equipment_names, condition, condition_value
                    )
                    logger.info(f"  Position check result: {len(pos_violations)} violations")
                    violations.extend(pos_violations)
                elif check_type == 'sequence':
                    violations.extend(self._check_dynamic_sequence(
                        rule, equipment_map, equipment_names, condition, condition_value
                    ))
                elif check_type == 'existence':
                    violations.extend(self._check_dynamic_existence(
                        rule, equipment_map, equipment_names, condition, condition_value
                    ))
                elif check_type == 'distance':
                    # 거리 검사는 스케일 정보 필요 - 수동 검토로 처리
                    logger.debug(f"Rule {rule_id}: distance check requires scale info")
                elif check_type == 'capacity':
                    # 용량 검사는 OCR 데이터 필요 - 수동 검토로 처리
                    logger.debug(f"Rule {rule_id}: capacity check requires OCR data")
                elif check_type == 'manual':
                    # 수동 검사는 위반 없음으로 처리 (Human-in-the-Loop에서 처리)
                    logger.debug(f"Rule {rule_id}: manual check - skipped")
            except Exception as e:
                logger.warning(f"Dynamic rule {rule_id} check failed: {e}")

        return violations

    def _check_dynamic_position(
        self,
        rule: Dict,
        equipment_map: Dict[str, Any],
        equipment_names: List[str],
        condition: str,
        condition_value: str
    ) -> List[BWMSViolation]:
        """동적 위치 규칙 검사"""
        violations = []

        if not equipment_names:
            return violations

        target_type = equipment_names[0].strip().upper()
        reference_type = condition_value.strip().upper() if condition_value else None

        # 대상 장비 찾기 (equipment_map은 {id: BWMSEquipment} 딕셔너리)
        target_equipment = [eq for eq in equipment_map.values()
                           if eq.equipment_type.value == target_type]
        reference_equipment = [eq for eq in equipment_map.values()
                              if eq.equipment_type.value == reference_type] if reference_type else []

        logger.debug(f"  Target type={target_type}, found {len(target_equipment)}")
        logger.debug(f"  Reference type={reference_type}, found {len(reference_equipment)}")

        for target in target_equipment:
            for ref in reference_equipment:
                is_violation = False

                if condition == 'above':
                    # target이 reference 위에 있어야 함 (y 좌표가 작아야 함)
                    if target.y >= ref.y:
                        is_violation = True
                elif condition == 'below':
                    if target.y <= ref.y:
                        is_violation = True
                elif condition == 'upstream_of':
                    # target이 reference 전단에 있어야 함 (x 좌표가 작아야 함)
                    if target.x >= ref.x:
                        is_violation = True
                elif condition == 'downstream_of':
                    if target.x <= ref.x:
                        is_violation = True

                if is_violation:
                    violations.append(BWMSViolation(
                        rule_id=rule.get('rule_id') or rule.get('id', 'UNKNOWN'),
                        rule_name=rule['name'],
                        rule_name_en=rule.get('name_en', rule['name']),
                        description=rule.get('description', ''),
                        severity=rule.get('severity', 'warning'),
                        standard=rule.get('standard', 'TECHCROSS BWMS Standard'),
                        location={"x": target.x, "y": target.y},
                        affected_elements=[target.id, ref.id] if ref else [target.id],
                        suggestion=rule.get('suggestion', f"{target_type} 위치를 확인하세요.")
                    ))

        return violations

    def _check_dynamic_sequence(
        self,
        rule: Dict,
        equipment_map: Dict[str, Any],
        equipment_names: List[str],
        condition: str,
        condition_value: str
    ) -> List[BWMSViolation]:
        """동적 순서 규칙 검사"""
        violations = []

        if len(equipment_names) < 2:
            return violations

        first_type = equipment_names[0].strip().upper()
        second_type = equipment_names[1].strip().upper() if len(equipment_names) > 1 else condition_value.strip().upper()

        # equipment_map은 {id: BWMSEquipment} 딕셔너리
        first_equipment = [eq for eq in equipment_map.values()
                         if eq.equipment_type.value == first_type]
        second_equipment = [eq for eq in equipment_map.values()
                          if eq.equipment_type.value == second_type]

        for first in first_equipment:
            for second in second_equipment:
                is_violation = False

                if condition == 'before':
                    # first가 second 앞에 있어야 함
                    if first.x >= second.x:
                        is_violation = True
                elif condition == 'after':
                    if first.x <= second.x:
                        is_violation = True

                if is_violation:
                    violations.append(BWMSViolation(
                        rule_id=rule.get('rule_id') or rule.get('id', 'UNKNOWN'),
                        rule_name=rule['name'],
                        rule_name_en=rule.get('name_en', rule['name']),
                        description=rule.get('description', ''),
                        severity=rule.get('severity', 'warning'),
                        standard=rule.get('standard', 'TECHCROSS BWMS Standard'),
                        location={"x": first.x, "y": first.y},
                        affected_elements=[first.id, second.id],
                        suggestion=rule.get('suggestion', f"{first_type}과 {second_type} 순서를 확인하세요.")
                    ))

        return violations

    def _check_dynamic_existence(
        self,
        rule: Dict,
        equipment_map: Dict[str, Any],
        equipment_names: List[str],
        condition: str,
        condition_value: str
    ) -> List[BWMSViolation]:
        """동적 존재 여부 규칙 검사"""
        violations = []

        if not equipment_names:
            return violations

        target_type = equipment_names[0].strip().upper()
        # equipment_map은 {id: BWMSEquipment} 딕셔너리
        found = any(eq.equipment_type.value == target_type for eq in equipment_map.values())

        if condition == 'required' and condition_value.lower() == 'true' and not found:
            violations.append(BWMSViolation(
                rule_id=rule.get('rule_id') or rule.get('id', 'UNKNOWN'),
                rule_name=rule['name'],
                rule_name_en=rule.get('name_en', rule['name']),
                description=rule.get('description', ''),
                severity=rule.get('severity', 'warning'),
                standard=rule.get('standard', 'TECHCROSS BWMS Standard'),
                location={"x": 0, "y": 0},
                affected_elements=[],
                suggestion=rule.get('suggestion', f"{target_type} 장비가 필요합니다.")
            ))

        return violations

    def run_all_checks(
        self,
        symbols: List[Dict],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None,
        texts: Optional[List[Dict]] = None,
        enabled_rules: Optional[List[str]] = None
    ) -> Tuple[List[BWMSViolation], Dict[str, Any]]:
        """모든 BWMS 규칙 검사 실행"""
        all_violations = []

        # 1. BWMS 장비 식별
        equipment_list = self.identify_bwms_equipment(symbols, texts)

        if not equipment_list:
            logger.info("No BWMS equipment found, skipping BWMS checks")
            return [], {"equipment_found": 0, "rules_checked": 0}

        # 2. 연결 그래프 구축
        equipment_map = self.build_flow_graph(equipment_list, connections, lines)

        # 3. 각 규칙 검사 실행
        rules_to_check = enabled_rules or list(self.rules.keys())

        if "BWMS-001" in rules_to_check:
            all_violations.extend(self.check_bwms_001_g2_sampling_port(equipment_map, symbols, texts))

        if "BWMS-004" in rules_to_check:
            all_violations.extend(self.check_bwms_004_fmu_ecu_sequence(equipment_map))

        if "BWMS-005" in rules_to_check:
            all_violations.extend(self.check_bwms_005_gds_position(equipment_map))

        if "BWMS-006" in rules_to_check:
            all_violations.extend(self.check_bwms_006_tsu_apu_distance(equipment_map))

        if "BWMS-007" in rules_to_check:
            all_violations.extend(self.check_bwms_007_mixing_pump_capacity(equipment_map, symbols, texts))

        if "BWMS-008" in rules_to_check:
            all_violations.extend(self.check_bwms_008_ecs_valve_position(equipment_map, symbols))

        if "BWMS-009" in rules_to_check:
            all_violations.extend(self.check_bwms_009_hychlor_filter(equipment_map, symbols))

        # 4. 동적 규칙 검사 (Excel 업로드된 규칙)
        dynamic_violations = self._check_dynamic_rules(
            equipment_map, symbols, connections, lines, texts, rules_to_check
        )
        all_violations.extend(dynamic_violations)

        # 동적 규칙 수 계산
        dynamic_rules_count = len(getattr(self, '_dynamic_rules', {}))

        # 요약 정보
        summary = {
            "equipment_found": len(equipment_list),
            "equipment_types": list(set(eq.equipment_type.value for eq in equipment_list)),
            "rules_checked": len(rules_to_check) + dynamic_rules_count,
            "builtin_rules": len(rules_to_check),
            "dynamic_rules": dynamic_rules_count,
            "violations_found": len(all_violations),
            "violations_by_severity": {
                "error": sum(1 for v in all_violations if v.severity == "error"),
                "warning": sum(1 for v in all_violations if v.severity == "warning"),
                "info": sum(1 for v in all_violations if v.severity == "info")
            }
        }

        logger.info(f"BWMS check complete: {len(all_violations)} violations found")
        return all_violations, summary


# Singleton instance
bwms_checker = BWMSChecker()
