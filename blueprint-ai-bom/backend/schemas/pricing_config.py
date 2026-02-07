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
    scrap_rate_round: float = 8.0    # 원형 소재 절삭 손실율 %
    scrap_rate_rect: float = 5.0     # 판재 절삭 손실율 %
    setup_cost: float = 50000        # 셋업비 (소량 고정비, KRW/품목)
    setup_qty_threshold: int = 5     # 이 수량 이하일 때 셋업비 부과
    inspection_rate: float = 3.0     # 검사비 (소계 대비 %)
    transport_per_kg: float = 50     # 운송비 (KRW/kg)


# 기본 단가 설정 (고객 자료 수령 시 교체 대상)
DEFAULT_PRICING_CONFIG = PricingConfig(
    materials=[
        # 일반구조강
        MaterialPrice(material="SS400", unit_price=850, density=7.85),
        MaterialPrice(material="SS275", unit_price=850, density=7.85),
        # 탄소강
        MaterialPrice(material="S20C", unit_price=1100, density=7.85),
        MaterialPrice(material="S45C", unit_price=1500, density=7.85),
        # 단조강
        MaterialPrice(material="SF440A", unit_price=1800, density=7.85),
        MaterialPrice(material="SF45A", unit_price=1800, density=7.85),
        MaterialPrice(material="A105", unit_price=1700, density=7.85),
        # 합금강
        MaterialPrice(material="SCM440", unit_price=2200, density=7.85),
        MaterialPrice(material="SM490A", unit_price=1000, density=7.85),
        # 스테인리스
        MaterialPrice(material="SUS304", unit_price=2800, density=7.93),
        MaterialPrice(material="SUS316", unit_price=3500, density=7.98),
        # 특수
        MaterialPrice(material="Babbitt", unit_price=60000, density=7.27),
        MaterialPrice(material="ASTM A193", unit_price=3500, density=7.85),
        MaterialPrice(material="ASTM A574", unit_price=3000, density=7.85),
        MaterialPrice(material="DEFAULT", unit_price=1500, density=7.85),
    ],
    allowances=[
        AllowanceRule(dimension_type="od", allowance_mm=5.0),
        AllowanceRule(dimension_type="id", allowance_mm=-3.0),
        AllowanceRule(dimension_type="length", allowance_mm=3.0),
    ],
    machining_rates=[
        # 정밀 가공 (베어링 계열: 공차 IT6~IT7, Ra 0.8~1.6)
        MachiningRate(part_type="BEARING", base_rate=80000),
        MachiningRate(part_type="BEARING RING", base_rate=70000),
        MachiningRate(part_type="BEARING CASING", base_rate=100000),
        MachiningRate(part_type="THRUST PAD", base_rate=60000),
        MachiningRate(part_type="LINER PAD", base_rate=55000),
        MachiningRate(part_type="ANTI WEAR PAD", base_rate=55000),
        MachiningRate(part_type="PAD", base_rate=50000),
        # 중정밀 (케이싱/하우징: 공차 IT7~IT8, Ra 1.6~3.2)
        MachiningRate(part_type="CASING", base_rate=100000),
        MachiningRate(part_type="THRUST CASING", base_rate=90000),
        MachiningRate(part_type="HOUSING", base_rate=100000),
        MachiningRate(part_type="BUSHING", base_rate=45000),
        MachiningRate(part_type="NOZZLE", base_rate=35000),
        MachiningRate(part_type="PIVOT", base_rate=40000),
        MachiningRate(part_type="COVER", base_rate=35000),
        # 일반 (링/플레이트: 공차 IT8~IT10, Ra 3.2~6.3)
        MachiningRate(part_type="RING", base_rate=30000),
        MachiningRate(part_type="SEAL RING", base_rate=35000),
        MachiningRate(part_type="SHAFT", base_rate=50000),
        MachiningRate(part_type="WEDGE", base_rate=25000),
        # 경가공 (심/플레이트: 공차 IT10~IT12, Ra 6.3~12.5)
        MachiningRate(part_type="PLATE", base_rate=15000),
        MachiningRate(part_type="SHIM", base_rate=10000),
        MachiningRate(part_type="SHIM PLATE", base_rate=10000),
        MachiningRate(part_type="LEVELING PLATE", base_rate=20000),
        MachiningRate(part_type="LOCKING PLATE", base_rate=15000),
        MachiningRate(part_type="DEFAULT", base_rate=40000),
    ],
)
