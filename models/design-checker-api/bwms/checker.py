"""
BWMS Checker Class
메인 검증기 클래스 - 모든 규칙 검사를 조율
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

from .base import (
    BWMSEquipment,
    BWMSViolation,
    BWMSEquipmentType,
    BWMS_EQUIPMENT_PATTERNS,
    BWMS_VALVE_PATTERNS,
    match_equipment_type,
    get_center,
    is_near,
)
from .rules_config import BWMS_DESIGN_RULES
from .equipment_identifier import identify_bwms_equipment, build_flow_graph
from .builtin_checks import (
    check_bwms_001_g2_sampling_port,
    check_bwms_004_fmu_ecu_sequence,
    check_bwms_005_gds_position,
    check_bwms_006_tsu_apu_distance,
    check_bwms_007_mixing_pump_capacity,
    check_bwms_008_ecs_valve_position,
    check_bwms_009_hychlor_filter,
)
from .dynamic_checks import check_dynamic_rules

logger = logging.getLogger(__name__)


class BWMSChecker:
    """BWMS P&ID 설계 검증기

    TECHCROSS BWMS 시스템의 P&ID 도면을 분석하고
    설계 규칙 위반을 검출합니다.

    Attributes:
        rules: 정적 규칙 딕셔너리
        equipment_patterns: 장비 패턴 딕셔너리
        valve_patterns: 밸브 패턴 목록
        _dynamic_rules: 동적으로 로드된 규칙 (Excel 업로드)
    """

    def __init__(self):
        self.rules = BWMS_DESIGN_RULES
        self.equipment_patterns = BWMS_EQUIPMENT_PATTERNS
        self.valve_patterns = BWMS_VALVE_PATTERNS
        self._dynamic_rules: Dict[str, Dict[str, Any]] = {}

    def identify_bwms_equipment(
        self,
        symbols: List[Dict],
        texts: Optional[List[Dict]] = None
    ) -> List[BWMSEquipment]:
        """심볼과 텍스트에서 BWMS 장비 식별

        Args:
            symbols: 검출된 심볼 목록
            texts: OCR로 추출된 텍스트 목록

        Returns:
            식별된 BWMS 장비 목록
        """
        return identify_bwms_equipment(symbols, texts, self.equipment_patterns)

    def _match_equipment_type(self, text: str):
        """텍스트에서 BWMS 장비 타입 매칭 (호환성용)"""
        return match_equipment_type(text, self.equipment_patterns)

    def _get_center(self, bbox):
        """bbox의 중심점 계산 (호환성용)"""
        return get_center(bbox)

    def _is_near(self, point1, point2, threshold=50):
        """두 점이 가까운지 확인 (호환성용)"""
        return is_near(point1, point2, threshold)

    def build_flow_graph(
        self,
        equipment_list: List[BWMSEquipment],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None
    ) -> Dict[str, BWMSEquipment]:
        """장비 연결 그래프 구축"""
        return build_flow_graph(equipment_list, connections, lines)

    def check_bwms_001_g2_sampling_port(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict],
        texts: Optional[List[Dict]] = None
    ) -> List[BWMSViolation]:
        """BWMS-001: G-2 Sampling Port 상류 위치 검증"""
        return check_bwms_001_g2_sampling_port(equipment_map, symbols, texts)

    def check_bwms_004_fmu_ecu_sequence(
        self,
        equipment_map: Dict[str, BWMSEquipment]
    ) -> List[BWMSViolation]:
        """BWMS-004: FMU-ECU 순서 검증"""
        return check_bwms_004_fmu_ecu_sequence(equipment_map)

    def check_bwms_005_gds_position(
        self,
        equipment_map: Dict[str, BWMSEquipment]
    ) -> List[BWMSViolation]:
        """BWMS-005: GDS 위치 검증"""
        return check_bwms_005_gds_position(equipment_map)

    def check_bwms_006_tsu_apu_distance(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        scale_factor: float = 1.0
    ) -> List[BWMSViolation]:
        """BWMS-006: TSU-APU 거리 제한 검증"""
        return check_bwms_006_tsu_apu_distance(equipment_map, scale_factor)

    def check_bwms_007_mixing_pump_capacity(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict],
        texts: Optional[List[Dict]] = None
    ) -> List[BWMSViolation]:
        """BWMS-007: Mixing Pump 용량 검증"""
        return check_bwms_007_mixing_pump_capacity(equipment_map, symbols, texts)

    def check_bwms_008_ecs_valve_position(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict]
    ) -> List[BWMSViolation]:
        """BWMS-008: ECS 밸브 위치 검증"""
        return check_bwms_008_ecs_valve_position(equipment_map, symbols, self.valve_patterns)

    def check_bwms_009_hychlor_filter(
        self,
        equipment_map: Dict[str, BWMSEquipment],
        symbols: List[Dict]
    ) -> List[BWMSViolation]:
        """BWMS-009: HYCHLOR 필터 위치 검증"""
        return check_bwms_009_hychlor_filter(equipment_map, symbols)

    def _should_apply_rule(self, rule: Dict, equipment_map: Dict[str, Any]) -> bool:
        """규칙이 현재 시스템 타입에 적용되어야 하는지 확인"""
        product_type = rule.get('product_type', 'ALL')
        if product_type == 'ALL':
            return True

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
        return check_dynamic_rules(
            equipment_map,
            symbols,
            connections,
            lines,
            texts,
            enabled_rules,
            self._dynamic_rules
        )

    def run_all_checks(
        self,
        symbols: List[Dict],
        connections: List[Dict],
        lines: Optional[List[Dict]] = None,
        texts: Optional[List[Dict]] = None,
        enabled_rules: Optional[List[str]] = None
    ) -> Tuple[List[BWMSViolation], Dict[str, Any]]:
        """모든 BWMS 규칙 검사 실행

        Args:
            symbols: 검출된 심볼 목록
            connections: 연결 정보 목록
            lines: 라인 정보 목록 (optional)
            texts: OCR 텍스트 목록 (optional)
            enabled_rules: 활성화할 규칙 ID 목록 (optional, None이면 전체)

        Returns:
            (위반 목록, 요약 정보) 튜플
        """
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
        dynamic_rules_count = len(self._dynamic_rules)

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
