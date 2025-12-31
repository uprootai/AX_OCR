"""
BWMS Base Types and Constants
Enum 정의, 데이터 클래스, 장비 패턴 정의
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


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
BWMS_EQUIPMENT_PATTERNS: Dict[BWMSEquipmentType, List[str]] = {
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
BWMS_VALVE_PATTERNS: List[str] = [
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
# Helper Functions
# =====================

def match_equipment_type(
    text: str,
    patterns: Dict[BWMSEquipmentType, List[str]] = None
) -> Optional[BWMSEquipmentType]:
    """텍스트에서 BWMS 장비 타입 매칭"""
    if patterns is None:
        patterns = BWMS_EQUIPMENT_PATTERNS

    text_upper = text.upper()

    for eq_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return eq_type

    return None


def get_center(bbox) -> Optional[Tuple[float, float]]:
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


def is_near(
    point1: Optional[Tuple[float, float]],
    point2: Optional[Tuple[float, float]],
    threshold: float = 50
) -> bool:
    """두 점이 가까운지 확인"""
    if not point1 or not point2:
        return False

    distance = ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5
    return distance < threshold
