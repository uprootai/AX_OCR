"""
BWMS Design Rules Configuration
정적 규칙 정의 딕셔너리
"""
from typing import Dict, Any

# =====================
# BWMS Design Rules
# =====================

BWMS_DESIGN_RULES: Dict[str, Dict[str, Any]] = {
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


def get_rule(rule_id: str) -> Dict[str, Any]:
    """규칙 ID로 규칙 정보 조회"""
    return BWMS_DESIGN_RULES.get(rule_id, {})


def get_all_rule_ids() -> list:
    """모든 규칙 ID 목록 반환"""
    return list(BWMS_DESIGN_RULES.keys())
