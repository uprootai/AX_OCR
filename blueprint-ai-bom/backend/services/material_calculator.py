"""Material Calculator - 재료비 계산 및 재질 정보 조회

Functions:
  - _get_material_info: 재질명으로 단가 정보 조회
  - calculate_material_cost: 재료비 = 중량 x 단가 x 수량
  - apply_allowance: 치수 + 여유치 → 소재 사이즈
  - _calc_quantity_discount: 수량 구간별 할인율
"""

import re
import logging
from typing import Dict, List

from schemas.pricing_config import (
    MaterialPrice,
    AllowanceRule,
)

logger = logging.getLogger(__name__)


def apply_allowance(
    dimensions: Dict[str, float],
    rules: List[AllowanceRule],
) -> Dict[str, float]:
    """치수 + 여유치 → 소재 사이즈

    OD 670 + 5mm → 675
    ID 440 - 3mm → 437 (allowance_mm이 음수)
    Length 190 + 3mm → 193
    """
    rule_map = {r.dimension_type: r.allowance_mm for r in rules}
    result = {}

    for key, value in dimensions.items():
        normalized = key.lower()
        allowance = rule_map.get(normalized, 0.0)
        # ID=0 (솔리드 부품)은 ID 여유치 미적용
        if normalized == "id" and value == 0:
            allowance = 0.0
        result[key] = value + allowance

    return result


def calculate_material_cost(
    weight_kg: float,
    unit_price: float,
    quantity: int,
) -> float:
    """재료비 = 중량 x 단가 x 수량"""
    return weight_kg * unit_price * quantity


def _get_material_info(
    material: str,
    materials: List[MaterialPrice],
) -> MaterialPrice:
    """재질명으로 단가 정보 조회 (부분 매칭 + 접미사 제거)"""
    material_upper = material.upper().strip()

    # 정확한 매칭
    for m in materials:
        if m.material.upper() == material_upper:
            return m

    # 접미사 제거 후 재매칭 (+QT, +N, +Q.T, OR EQV 등)
    cleaned = re.sub(r'[\+\s]*(Q\.?T|QT|N|OR\s+EQV).*$', '', material_upper).strip()
    if cleaned != material_upper:
        for m in materials:
            if m.material.upper() == cleaned:
                return m

    # 부분 매칭 (SS400이 "SS400 (KS)" 같은 형태에도 매칭)
    for m in materials:
        if m.material.upper() in material_upper or material_upper in m.material.upper():
            return m

    # 기본값
    for m in materials:
        if m.material.upper() == "DEFAULT":
            return m

    return MaterialPrice(material="DEFAULT", unit_price=1500, density=7.85)


def _calc_quantity_discount(quantity: int) -> float:
    """수량 구간별 할인율 (%)"""
    if quantity >= 100:
        return 15.0
    elif quantity >= 50:
        return 10.0
    elif quantity >= 10:
        return 5.0
    return 0.0
