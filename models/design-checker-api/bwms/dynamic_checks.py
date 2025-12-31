"""
BWMS Dynamic Rule Checks
동적으로 로드된 규칙 (Excel 업로드) 검사 로직
"""
import logging
from typing import List, Dict, Any, Optional

from .base import BWMSEquipment, BWMSViolation

logger = logging.getLogger(__name__)


def should_apply_rule(
    rule: Dict[str, Any],
    equipment_map: Dict[str, BWMSEquipment]
) -> bool:
    """규칙이 현재 시스템 타입에 적용되어야 하는지 확인

    Args:
        rule: 규칙 정의 딕셔너리
        equipment_map: 장비 맵

    Returns:
        규칙 적용 여부
    """
    product_type = rule.get('product_type', 'ALL')
    if product_type == 'ALL':
        return True

    # 시스템 타입 추론 (HGU 있으면 HYCHLOR, 아니면 ECS)
    has_hgu = any(eq.equipment_type.value == 'HGU' for eq in equipment_map.values())
    current_system = 'HYCHLOR' if has_hgu else 'ECS'

    return product_type == current_system


def check_dynamic_position(
    rule: Dict[str, Any],
    equipment_map: Dict[str, BWMSEquipment],
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

    # 대상 장비 찾기
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


def check_dynamic_sequence(
    rule: Dict[str, Any],
    equipment_map: Dict[str, BWMSEquipment],
    equipment_names: List[str],
    condition: str,
    condition_value: str
) -> List[BWMSViolation]:
    """동적 순서 규칙 검사"""
    violations = []

    if len(equipment_names) < 2:
        return violations

    first_type = equipment_names[0].strip().upper()
    second_type = (
        equipment_names[1].strip().upper()
        if len(equipment_names) > 1
        else condition_value.strip().upper()
    )

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


def check_dynamic_existence(
    rule: Dict[str, Any],
    equipment_map: Dict[str, BWMSEquipment],
    equipment_names: List[str],
    condition: str,
    condition_value: str
) -> List[BWMSViolation]:
    """동적 존재 여부 규칙 검사"""
    violations = []

    if not equipment_names:
        return violations

    target_type = equipment_names[0].strip().upper()
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


def check_dynamic_rules(
    equipment_map: Dict[str, BWMSEquipment],
    symbols: List[Dict],
    connections: List[Dict],
    lines: Optional[List[Dict]],
    texts: Optional[List[Dict]],
    enabled_rules: List[str],
    dynamic_rules: Dict[str, Dict[str, Any]]
) -> List[BWMSViolation]:
    """동적으로 로드된 규칙 검사 (Excel 업로드)

    Args:
        equipment_map: 장비 맵
        symbols: 심볼 목록
        connections: 연결 정보
        lines: 라인 정보 (optional)
        texts: 텍스트 정보 (optional)
        enabled_rules: 활성화된 규칙 ID 목록
        dynamic_rules: 동적 규칙 딕셔너리

    Returns:
        위반 목록
    """
    violations = []

    if not dynamic_rules:
        logger.debug("No dynamic rules loaded")
        return violations

    logger.info(f"Checking {len(dynamic_rules)} dynamic rules")

    for rule_id, rule in dynamic_rules.items():
        # product_type 필터링: 현재 시스템에 해당하는 규칙만 적용
        if not should_apply_rule(rule, equipment_map):
            logger.debug(f"Skipping rule {rule_id}: product_type mismatch")
            continue

        check_type = rule.get('check_type', 'manual')
        equipment_names = rule.get('equipment', '').split(',') if rule.get('equipment') else []
        condition = rule.get('condition', '')
        condition_value = rule.get('condition_value', '')

        try:
            logger.info(f"Processing dynamic rule: {rule_id} (type={check_type}, equipment={equipment_names})")

            if check_type == 'position':
                pos_violations = check_dynamic_position(
                    rule, equipment_map, equipment_names, condition, condition_value
                )
                logger.info(f"  Position check result: {len(pos_violations)} violations")
                violations.extend(pos_violations)

            elif check_type == 'sequence':
                violations.extend(check_dynamic_sequence(
                    rule, equipment_map, equipment_names, condition, condition_value
                ))

            elif check_type == 'existence':
                violations.extend(check_dynamic_existence(
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
