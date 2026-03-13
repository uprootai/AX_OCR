"""
Price Database — 데이터 모델 (dataclasses)
"""

from dataclasses import dataclass


@dataclass
class MaterialPrice:
    """재질 가격 정보"""
    code: str
    name_kr: str
    name_en: str
    price_per_kg: float  # KRW/kg
    category: str  # steel, babbitt, stainless, etc.
    description: str = ""


@dataclass
class LaborCost:
    """가공비 정보"""
    part_type: str
    base_cost: float  # KRW
    complexity_factor: float = 1.0  # 복잡도 계수
    description: str = ""


@dataclass
class CustomerConfig:
    """고객별 설정"""
    customer_id: str
    customer_name: str
    material_discount: float = 0.0  # 재질 할인율
    labor_discount: float = 0.0  # 가공비 할인율
    payment_terms: int = 30  # 결제 조건 (일)
    currency: str = "KRW"
