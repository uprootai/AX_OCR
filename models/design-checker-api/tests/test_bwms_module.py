"""
BWMS Module Unit Tests
BWMS 설계 규칙 패키지 테스트
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBWMSEquipmentType:
    """BWMSEquipmentType Enum 테스트"""

    def test_equipment_type_enum_exists(self):
        """Enum 존재 확인"""
        from bwms import BWMSEquipmentType

        assert BWMSEquipmentType is not None

    def test_ecs_equipment_types(self):
        """ECS 시스템 장비 타입"""
        from bwms import BWMSEquipmentType

        ecs_types = [
            BWMSEquipmentType.ECU,
            BWMSEquipmentType.FMU,
            BWMSEquipmentType.ANU,
            BWMSEquipmentType.TSU,
            BWMSEquipmentType.APU,
            BWMSEquipmentType.GDS,
        ]

        for eq_type in ecs_types:
            assert eq_type.value is not None

    def test_hychlor_equipment_types(self):
        """HYCHLOR 시스템 장비 타입"""
        from bwms import BWMSEquipmentType

        hychlor_types = [
            BWMSEquipmentType.HGU,
            BWMSEquipmentType.DMU,
            BWMSEquipmentType.NIU,
            BWMSEquipmentType.DTS,
        ]

        for eq_type in hychlor_types:
            assert eq_type.value is not None


class TestBWMSEquipmentPatterns:
    """BWMS 장비 패턴 테스트"""

    def test_equipment_patterns_exists(self):
        """패턴 딕셔너리 존재"""
        from bwms import BWMS_EQUIPMENT_PATTERNS

        assert BWMS_EQUIPMENT_PATTERNS is not None
        assert isinstance(BWMS_EQUIPMENT_PATTERNS, dict)

    def test_valve_patterns_exists(self):
        """밸브 패턴 리스트 존재"""
        from bwms import BWMS_VALVE_PATTERNS

        assert BWMS_VALVE_PATTERNS is not None
        assert isinstance(BWMS_VALVE_PATTERNS, list)
        assert len(BWMS_VALVE_PATTERNS) >= 5


class TestMatchEquipmentType:
    """match_equipment_type 함수 테스트"""

    def test_match_ecu(self):
        """ECU 매칭"""
        from bwms import match_equipment_type, BWMSEquipmentType

        result = match_equipment_type("ECU-01")
        assert result == BWMSEquipmentType.ECU

    def test_match_fmu(self):
        """FMU 매칭"""
        from bwms import match_equipment_type, BWMSEquipmentType

        result = match_equipment_type("FMU-02")
        assert result == BWMSEquipmentType.FMU

    def test_match_electrolyzer(self):
        """ELECTROLYZER 키워드 매칭"""
        from bwms import match_equipment_type, BWMSEquipmentType

        result = match_equipment_type("ELECTROLYZER UNIT")
        assert result == BWMSEquipmentType.ECU

    def test_no_match(self):
        """매칭 없음"""
        from bwms import match_equipment_type

        result = match_equipment_type("RANDOM TEXT")
        assert result is None


class TestGetCenter:
    """get_center 함수 테스트"""

    def test_get_center_xyxy_format(self):
        """[x1, y1, x2, y2] 형식"""
        from bwms import get_center

        bbox = [0, 0, 100, 100]
        center = get_center(bbox)
        assert center == (50.0, 50.0)

    def test_get_center_polygon_format(self):
        """[[x,y], ...] 형식"""
        from bwms import get_center

        bbox = [[0, 0], [100, 0], [100, 100], [0, 100]]
        center = get_center(bbox)
        assert center == (50.0, 50.0)

    def test_get_center_empty(self):
        """빈 bbox"""
        from bwms import get_center

        result = get_center([])
        assert result is None

    def test_get_center_none(self):
        """None bbox"""
        from bwms import get_center

        result = get_center(None)
        assert result is None


class TestIsNear:
    """is_near 함수 테스트"""

    def test_is_near_true(self):
        """가까운 두 점"""
        from bwms import is_near

        result = is_near((0, 0), (10, 10), threshold=50)
        assert result is True

    def test_is_near_false(self):
        """먼 두 점"""
        from bwms import is_near

        result = is_near((0, 0), (100, 100), threshold=50)
        assert result is False

    def test_is_near_none_point(self):
        """None 포인트"""
        from bwms import is_near

        assert is_near(None, (0, 0)) is False
        assert is_near((0, 0), None) is False


class TestBWMSEquipmentDataclass:
    """BWMSEquipment 데이터클래스 테스트"""

    def test_create_equipment(self):
        """장비 객체 생성"""
        from bwms import BWMSEquipment, BWMSEquipmentType

        eq = BWMSEquipment(
            id="eq-001",
            equipment_type=BWMSEquipmentType.ECU,
            label="ECU-01",
            x=100.0,
            y=200.0
        )

        assert eq.id == "eq-001"
        assert eq.equipment_type == BWMSEquipmentType.ECU
        assert eq.label == "ECU-01"

    def test_equipment_default_fields(self):
        """기본값 필드"""
        from bwms import BWMSEquipment, BWMSEquipmentType

        eq = BWMSEquipment(
            id="eq-001",
            equipment_type=BWMSEquipmentType.ECU,
            label="ECU-01",
            x=100.0,
            y=200.0
        )

        assert eq.width == 0
        assert eq.height == 0
        assert eq.bbox == []
        assert eq.connected_to == []


class TestBWMSViolationDataclass:
    """BWMSViolation 데이터클래스 테스트"""

    def test_create_violation(self):
        """위반 객체 생성"""
        from bwms import BWMSViolation

        violation = BWMSViolation(
            rule_id="BWMS-001",
            rule_name="G-2 샘플링 포트 위치",
            rule_name_en="G-2 Sampling Port Position",
            description="G-2 샘플링 포트가 ECU 상류에 있어야 합니다",
            severity="error",
            standard="TECHCROSS"
        )

        assert violation.rule_id == "BWMS-001"
        assert violation.severity == "error"


class TestRulesConfig:
    """규칙 설정 테스트"""

    def test_bwms_design_rules_exists(self):
        """BWMS_DESIGN_RULES 딕셔너리 존재"""
        from bwms import BWMS_DESIGN_RULES

        assert BWMS_DESIGN_RULES is not None
        assert isinstance(BWMS_DESIGN_RULES, dict)

    def test_get_rule_function(self):
        """get_rule 함수"""
        from bwms import get_rule

        # BWMS-001은 대부분 정의되어 있음
        rule = get_rule("BWMS-001")
        # 규칙이 있으면 dict 반환, 없으면 None
        assert rule is None or isinstance(rule, dict)

    def test_get_all_rule_ids(self):
        """get_all_rule_ids 함수"""
        from bwms import get_all_rule_ids

        rule_ids = get_all_rule_ids()
        assert isinstance(rule_ids, list)


class TestBuiltinChecks:
    """내장 체크 함수 존재 테스트"""

    def test_check_functions_exist(self):
        """체크 함수들 존재"""
        from bwms import (
            check_bwms_001_g2_sampling_port,
            check_bwms_004_fmu_ecu_sequence,
            check_bwms_005_gds_position,
            check_bwms_006_tsu_apu_distance,
            check_bwms_007_mixing_pump_capacity,
            check_bwms_008_ecs_valve_position,
            check_bwms_009_hychlor_filter,
        )

        assert check_bwms_001_g2_sampling_port is not None
        assert check_bwms_004_fmu_ecu_sequence is not None
        assert check_bwms_005_gds_position is not None
        assert check_bwms_006_tsu_apu_distance is not None
        assert check_bwms_007_mixing_pump_capacity is not None
        assert check_bwms_008_ecs_valve_position is not None
        assert check_bwms_009_hychlor_filter is not None


class TestDynamicChecks:
    """동적 체크 함수 존재 테스트"""

    def test_dynamic_check_functions_exist(self):
        """동적 체크 함수들 존재"""
        from bwms import (
            should_apply_rule,
            check_dynamic_position,
            check_dynamic_sequence,
            check_dynamic_existence,
            check_dynamic_rules,
        )

        assert should_apply_rule is not None
        assert check_dynamic_position is not None
        assert check_dynamic_sequence is not None
        assert check_dynamic_existence is not None
        assert check_dynamic_rules is not None


class TestBWMSChecker:
    """BWMSChecker 클래스 테스트"""

    def test_bwms_checker_class_exists(self):
        """BWMSChecker 클래스 존재"""
        from bwms import BWMSChecker

        assert BWMSChecker is not None

    def test_bwms_checker_singleton(self):
        """bwms_checker 싱글턴"""
        from bwms import bwms_checker

        assert bwms_checker is not None


class TestModuleExports:
    """모듈 __all__ 내보내기 테스트"""

    def test_all_exports(self):
        """__all__ 내보내기 확인"""
        import bwms

        expected_exports = [
            "BWMSEquipmentType",
            "BWMSEquipment",
            "BWMSViolation",
            "BWMS_EQUIPMENT_PATTERNS",
            "BWMS_VALVE_PATTERNS",
            "match_equipment_type",
            "get_center",
            "is_near",
            "BWMSChecker",
            "bwms_checker",
        ]

        for export_name in expected_exports:
            assert hasattr(bwms, export_name), f"Missing export: {export_name}"
