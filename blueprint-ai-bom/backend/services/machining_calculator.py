"""Machining Calculator - 가공비, 난이도 계수, 열처리/표면처리 비용

Functions:
  - _detect_part_type: 부품명에서 부품 유형 추출
  - _calc_difficulty_factor: 가공 난이도 계수 산출
  - calculate_machining_cost: 가공비 = 기본가공비 × 크기계수 × 난이도계수 × 수량
  - _detect_treatments: 열처리/표면처리 항목 검출
  - _calc_treatment_cost: 열처리/표면처리 비용 합산
"""

import logging
from typing import Dict, List, Optional

from schemas.pricing_config import MachiningRate

logger = logging.getLogger(__name__)


def _detect_part_type(description: str) -> str:
    """부품명에서 부품 유형 추출 (긴 키워드 우선 매칭)"""
    desc_upper = description.upper()
    # 긴 키워드 먼저 (BEARING RING → BEARING, SHIM PLATE → SHIM)
    _PART_KEYWORDS = [
        "BEARING CASING", "BEARING RING", "BEARING",
        "THRUST CASING", "CASING",
        "HOUSING",
        "LEVELING PLATE", "SHIM PLATE", "LOCKING PLATE",
        "THRUST PAD", "LINER PAD", "ANTI WEAR PAD", "PAD",
        "SEAL RING", "RING",
        "WEDGE", "NOZZLE", "BUSHING", "PIVOT", "COVER",
        "SHAFT", "PLATE", "SHIM",
    ]
    for keyword in _PART_KEYWORDS:
        if keyword in desc_upper:
            return keyword
    return "DEFAULT"


# 가공 난이도 키워드 → 추가 계수 (누적)
_DIFFICULTY_KEYWORDS: Dict[str, float] = {
    "KEYWAY": 0.3,      # 키홈 가공
    "KEY WAY": 0.3,
    "GROOVE": 0.2,      # 홈 가공
    "THREAD": 0.2,      # 나사 가공
    "TAPPING": 0.2,
    "GRINDING": 0.3,    # 연삭 가공
    "LAPPING": 0.4,     # 래핑 (정밀)
    "BORING": 0.2,      # 보링 가공
    "SLOT": 0.15,       # 슬롯
    "HOLE": 0.1,        # 홀 가공
    "CHAMFER": 0.05,    # 면취
    "ASSY": 0.15,       # 조립 공수
    "ASSEMBLY": 0.15,
}


def _calc_difficulty_factor(
    description: str, material: str,
    dimensions: Optional[Dict[str, float]] = None,
) -> float:
    """부품 설명 + 재질 + 치수에서 가공 난이도 계수 산출 (기본 1.0)"""
    desc_upper = description.upper()
    mat_upper = material.upper()

    factor = 1.0

    # 키워드별 누적 가산
    for keyword, add in _DIFFICULTY_KEYWORDS.items():
        if keyword in desc_upper:
            factor += add

    # 난삭재 가산
    if "SUS" in mat_upper or "STAINLESS" in mat_upper:
        factor += 0.3
    elif "SCM" in mat_upper or "SNCM" in mat_upper:
        factor += 0.15
    elif "BABBITT" in mat_upper:
        factor += 0.2

    # 치수 기반 가산 (원형 부품)
    if dimensions:
        od = dimensions.get("od", 0)
        id_ = dimensions.get("id", 0)
        if od > 0 and id_ > 0:
            wall_ratio = id_ / od  # 벽두께 비율
            if wall_ratio > 0.85:       # 극박 (벽 7.5% 미만)
                factor += 0.4
            elif wall_ratio > 0.75:     # 박벽 (벽 12.5% 미만)
                factor += 0.2
        # 대형 부품 (OD > 800mm)
        if od > 800:
            factor += 0.15

    return min(factor, 3.0)  # 상한 3배


def calculate_machining_cost(
    part_type: str,
    rates: List[MachiningRate],
    quantity: int,
    weight_kg: float = 0.0,
    difficulty_factor: float = 1.0,
) -> float:
    """가공비 = 기본가공비 × 크기계수 × 난이도계수 × 수량"""
    rate_map = {r.part_type.upper(): r.base_rate for r in rates}
    base_rate = rate_map.get(part_type.upper(), rate_map.get("DEFAULT", 40000))

    # 중량 기반 크기계수 (5단계)
    if weight_kg < 1:
        size_factor = 0.3
    elif weight_kg < 10:
        size_factor = 0.5
    elif weight_kg < 50:
        size_factor = 1.0
    elif weight_kg < 200:
        size_factor = 1.5
    else:
        size_factor = 2.0

    return base_rate * size_factor * difficulty_factor * quantity


# 열처리/표면처리 단가 (KRW/kg)
_TREATMENT_COSTS: Dict[str, float] = {
    "QT": 800,           # 조질 (담금질+뜨임)
    "Q.T": 800,
    "QUENCHING": 800,
    "TEMPERING": 500,
    "NORMALIZING": 400,  # 노멀라이징
    "CARBURIZING": 1200, # 침탄
    "NITRIDING": 1500,   # 질화
    "INDUCTION": 1000,   # 고주파 열처리
    "CHROME": 2000,      # 크롬 도금
    "HARD CHROME": 2500,
    "SPRAY": 3000,       # 용사 코팅
    "BABBITT LINING": 5000,  # 배빗 라이닝
}


def _detect_treatments(description: str, material: str) -> List[str]:
    """재질명 + 설명에서 열처리/표면처리 항목 검출 (긴 키워드 우선, 중복 제거)"""
    combined = f"{material} {description}".upper()
    found = []
    # 긴 키워드 우선 매칭 (HARD CHROME > CHROME)
    for treatment in sorted(_TREATMENT_COSTS.keys(), key=len, reverse=True):
        if treatment in combined:
            # 이미 상위 키워드가 잡혔으면 하위 키워드 스킵
            if any(treatment in existing for existing in found):
                continue
            found.append(treatment)
    return found


def _calc_treatment_cost(treatments: List[str], weight_kg: float, quantity: int) -> float:
    """열처리/표면처리 비용 합산"""
    total = 0.0
    for t in treatments:
        rate = _TREATMENT_COSTS.get(t, 0)
        total += rate * weight_kg * quantity
    return total
