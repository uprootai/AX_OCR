"""Pricing Config Schemas - 단가 설정 스키마

Phase 4: 기본 단가로 견적 계산 → 고객 자료 수령 시 교체
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MaterialPrice(BaseModel):
    """재질별 단가"""
    material: str
    unit_price: float          # KRW/kg
    density: float = 7.85      # kg/dm3 (철강 기본)


class AllowanceRule(BaseModel):
    """여유치 규칙"""
    dimension_type: str        # "od" | "id" | "length"
    allowance_mm: float        # 가공 여유 (mm)


class MachiningRate(BaseModel):
    """가공비 단가"""
    part_type: str             # "PAD", "RING", "CASING", ...
    base_rate: float           # KRW/개


class PricingConfig(BaseModel):
    """프로젝트 단가 설정"""
    materials: List[MaterialPrice] = Field(default_factory=list)
    allowances: List[AllowanceRule] = Field(default_factory=list)
    machining_rates: List[MachiningRate] = Field(default_factory=list)
    material_margin: float = 15.0    # 재료비 마진 %
    labor_margin: float = 20.0       # 가공비 마진 %
    tax_rate: float = 10.0           # 세율 %


# 기본 단가 설정 (고객 자료 수령 시 교체 대상)
DEFAULT_PRICING_CONFIG = PricingConfig(
    materials=[
        MaterialPrice(material="SS400", unit_price=3500, density=7.85),
        MaterialPrice(material="SS275", unit_price=3500, density=7.85),
        MaterialPrice(material="SF440A", unit_price=5000, density=7.85),
        MaterialPrice(material="SF45A", unit_price=5000, density=7.85),
        MaterialPrice(material="S45C", unit_price=4000, density=7.85),
        MaterialPrice(material="SCM440", unit_price=6000, density=7.85),
        MaterialPrice(material="SUS304", unit_price=12000, density=7.93),
        MaterialPrice(material="SUS316", unit_price=15000, density=7.98),
        MaterialPrice(material="Babbitt", unit_price=45000, density=7.27),
        MaterialPrice(material="DEFAULT", unit_price=5000, density=7.85),
    ],
    allowances=[
        AllowanceRule(dimension_type="od", allowance_mm=10.0),
        AllowanceRule(dimension_type="id", allowance_mm=-5.0),
        AllowanceRule(dimension_type="length", allowance_mm=5.0),
    ],
    machining_rates=[
        MachiningRate(part_type="PAD", base_rate=50000),
        MachiningRate(part_type="RING", base_rate=30000),
        MachiningRate(part_type="BEARING", base_rate=80000),
        MachiningRate(part_type="CASING", base_rate=100000),
        MachiningRate(part_type="HOUSING", base_rate=100000),
        MachiningRate(part_type="DEFAULT", base_rate=40000),
    ],
)
