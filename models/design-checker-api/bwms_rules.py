"""
BWMS (Ballast Water Management System) 설계 규칙
TECHCROSS P&ID 설계 검증용 규칙 모듈

규칙 목록:
- BWMS-001: G-2 Sampling Port 상류(upstream) 위치 확인
- BWMS-004: FMU가 ECU 후단에 위치 확인
- BWMS-005: GDS가 ECU/HGU 상부에 위치 확인
- BWMS-006: TSU-APU 근접 확인 (5m 이내) - 스케일 필요
- BWMS-007: Mixing Pump = Ballast Pump x 4.3% 확인
- BWMS-008: ECS 밸브 위치 확인
- BWMS-009: HYCHLOR 필터 위치 확인

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 bwms/ 패키지에 있습니다.
"""

# Re-export everything from the bwms package
from bwms import (
    # Base types
    BWMSEquipmentType,
    BWMSEquipment,
    BWMSViolation,
    BWMS_EQUIPMENT_PATTERNS,
    BWMS_VALVE_PATTERNS,
    match_equipment_type,
    get_center,
    is_near,
    # Rules config
    BWMS_DESIGN_RULES,
    get_rule,
    get_all_rule_ids,
    # Equipment identifier
    identify_bwms_equipment,
    build_flow_graph,
    # Built-in checks
    check_bwms_001_g2_sampling_port,
    check_bwms_004_fmu_ecu_sequence,
    check_bwms_005_gds_position,
    check_bwms_006_tsu_apu_distance,
    check_bwms_007_mixing_pump_capacity,
    check_bwms_008_ecs_valve_position,
    check_bwms_009_hychlor_filter,
    # Dynamic checks
    should_apply_rule,
    check_dynamic_position,
    check_dynamic_sequence,
    check_dynamic_existence,
    check_dynamic_rules,
    # Checker
    BWMSChecker,
    bwms_checker,
)

__all__ = [
    # Base types
    "BWMSEquipmentType",
    "BWMSEquipment",
    "BWMSViolation",
    "BWMS_EQUIPMENT_PATTERNS",
    "BWMS_VALVE_PATTERNS",
    "match_equipment_type",
    "get_center",
    "is_near",
    # Rules config
    "BWMS_DESIGN_RULES",
    "get_rule",
    "get_all_rule_ids",
    # Equipment identifier
    "identify_bwms_equipment",
    "build_flow_graph",
    # Built-in checks
    "check_bwms_001_g2_sampling_port",
    "check_bwms_004_fmu_ecu_sequence",
    "check_bwms_005_gds_position",
    "check_bwms_006_tsu_apu_distance",
    "check_bwms_007_mixing_pump_capacity",
    "check_bwms_008_ecs_valve_position",
    "check_bwms_009_hychlor_filter",
    # Dynamic checks
    "should_apply_rule",
    "check_dynamic_position",
    "check_dynamic_sequence",
    "check_dynamic_existence",
    "check_dynamic_rules",
    # Checker
    "BWMSChecker",
    "bwms_checker",
]
