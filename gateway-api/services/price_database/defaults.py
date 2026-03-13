"""
Price Database — 기본값 데이터 (재질, 가공비, 수량할인, 고객)
"""

from typing import Dict, List, Tuple
from .models import MaterialPrice, LaborCost, CustomerConfig


# 기본 재질 단가 (KRW/kg)
DEFAULT_MATERIAL_PRICES: Dict[str, MaterialPrice] = {
    "SF45A": MaterialPrice(
        code="SF45A",
        name_kr="단조강 SF45A",
        name_en="Forged Steel SF45A",
        price_per_kg=5000,
        category="steel",
        description="베어링 링, 케이싱용 범용 단조강"
    ),
    "SF440A": MaterialPrice(
        code="SF440A",
        name_kr="단조강 SF440A",
        name_en="Forged Steel SF440A",
        price_per_kg=5500,
        category="steel",
        description="고강도 단조강"
    ),
    "SM490A": MaterialPrice(
        code="SM490A",
        name_kr="용접구조용 SM490A",
        name_en="Welding Structure SM490A",
        price_per_kg=4800,
        category="steel"
    ),
    "S45C": MaterialPrice(
        code="S45C",
        name_kr="기계구조용탄소강 S45C",
        name_en="Carbon Steel S45C",
        price_per_kg=4500,
        category="steel"
    ),
    "S45C-N": MaterialPrice(
        code="S45C-N",
        name_kr="기계구조용탄소강 S45C-N (질화)",
        name_en="Carbon Steel S45C-N (Nitrided)",
        price_per_kg=4800,
        category="steel"
    ),
    "SS400": MaterialPrice(
        code="SS400",
        name_kr="일반구조용압연강 SS400",
        name_en="Rolled Steel SS400",
        price_per_kg=3500,
        category="steel"
    ),
    "STS304": MaterialPrice(
        code="STS304",
        name_kr="스테인리스강 STS304",
        name_en="Stainless Steel STS304",
        price_per_kg=12000,
        category="stainless"
    ),
    "STS316": MaterialPrice(
        code="STS316",
        name_kr="스테인리스강 STS316",
        name_en="Stainless Steel STS316",
        price_per_kg=15000,
        category="stainless"
    ),
    "SCM435": MaterialPrice(
        code="SCM435",
        name_kr="크롬몰리브덴강 SCM435",
        name_en="Chromium-Molybdenum Steel SCM435",
        price_per_kg=7000,
        category="alloy"
    ),
    "ASTM_B23_GR2": MaterialPrice(
        code="ASTM B23 GR.2",
        name_kr="배빗메탈 ASTM B23 GR.2",
        name_en="Babbitt Metal ASTM B23 GR.2",
        price_per_kg=45000,
        category="babbitt",
        description="스러스트 베어링 라이닝용 백색 합금"
    ),
    "ASTM_A193_B7": MaterialPrice(
        code="ASTM A193 B7",
        name_kr="고온용 볼트 재질",
        name_en="High Temp Bolt Material",
        price_per_kg=8000,
        category="alloy"
    ),
    "CF450A": MaterialPrice(
        code="CF450A",
        name_kr="주조강 CF450A",
        name_en="Cast Steel CF450A",
        price_per_kg=5200,
        category="cast"
    ),
    # ========== PANASIA BWMS 재질 ==========
    "STS316L": MaterialPrice(
        code="STS316L",
        name_kr="스테인리스강 STS316L",
        name_en="Stainless Steel STS316L",
        price_per_kg=16000,
        category="stainless",
        description="해수 내식성 우수, BWMS 핵심 재질"
    ),
    "STS304L": MaterialPrice(
        code="STS304L",
        name_kr="스테인리스강 STS304L",
        name_en="Stainless Steel STS304L",
        price_per_kg=13000,
        category="stainless",
        description="저탄소 스테인리스, 용접성 우수"
    ),
    "TITANIUM_GR2": MaterialPrice(
        code="TITANIUM GR2",
        name_kr="티타늄 Grade 2",
        name_en="Titanium Grade 2",
        price_per_kg=85000,
        category="titanium",
        description="해수 완전 내식, BWMS 고급 사양"
    ),
    "AL5083": MaterialPrice(
        code="AL5083",
        name_kr="알루미늄 합금 AL5083",
        name_en="Aluminum Alloy AL5083",
        price_per_kg=8500,
        category="aluminum",
        description="해양용 알루미늄, 내식성 우수"
    ),
    "CPVC": MaterialPrice(
        code="CPVC",
        name_kr="CPVC (염화폴리염화비닐)",
        name_en="Chlorinated PVC",
        price_per_kg=4500,
        category="plastic",
        description="내화학성 파이프 재질"
    ),
    "HDPE": MaterialPrice(
        code="HDPE",
        name_kr="HDPE (고밀도폴리에틸렌)",
        name_en="High-Density Polyethylene",
        price_per_kg=3000,
        category="plastic",
        description="해양용 파이프, 경량 내식"
    ),
    "SUPER_DUPLEX": MaterialPrice(
        code="SUPER DUPLEX",
        name_kr="슈퍼 듀플렉스강",
        name_en="Super Duplex Stainless Steel",
        price_per_kg=35000,
        category="stainless",
        description="고강도 해수 내식 특수강"
    ),
    "BRONZE_ALBZ": MaterialPrice(
        code="BRONZE ALBZ",
        name_kr="알루미늄 청동",
        name_en="Aluminum Bronze",
        price_per_kg=28000,
        category="bronze",
        description="해양 밸브/펌프용 청동"
    ),
    "INCONEL_625": MaterialPrice(
        code="INCONEL 625",
        name_kr="인코넬 625",
        name_en="Inconel 625",
        price_per_kg=120000,
        category="superalloy",
        description="극한 내식성, BWMS 특수 부품"
    ),
}


# 기본 가공비 (KRW)
DEFAULT_LABOR_COSTS: Dict[str, LaborCost] = {
    "RING": LaborCost(
        part_type="RING",
        base_cost=80000,
        complexity_factor=1.0,
        description="베어링 링 가공"
    ),
    "BEARING": LaborCost(
        part_type="BEARING",
        base_cost=100000,
        complexity_factor=1.2,
        description="베어링 조립체"
    ),
    "CASING": LaborCost(
        part_type="CASING",
        base_cost=120000,
        complexity_factor=1.3,
        description="케이싱 가공"
    ),
    "PAD": LaborCost(
        part_type="PAD",
        base_cost=50000,
        complexity_factor=0.8,
        description="패드 가공"
    ),
    "BOLT": LaborCost(
        part_type="BOLT",
        base_cost=5000,
        complexity_factor=0.3,
        description="볼트류"
    ),
    "NUT": LaborCost(
        part_type="NUT",
        base_cost=3000,
        complexity_factor=0.2,
        description="너트류"
    ),
    "PIN": LaborCost(
        part_type="PIN",
        base_cost=8000,
        complexity_factor=0.4,
        description="핀류"
    ),
    "WASHER": LaborCost(
        part_type="WASHER",
        base_cost=2000,
        complexity_factor=0.1,
        description="와셔류"
    ),
    "PLATE": LaborCost(
        part_type="PLATE",
        base_cost=15000,
        complexity_factor=0.5,
        description="플레이트"
    ),
    "SHIM": LaborCost(
        part_type="SHIM",
        base_cost=10000,
        complexity_factor=0.4,
        description="심 플레이트"
    ),
    "ASSY": LaborCost(
        part_type="ASSY",
        base_cost=150000,
        complexity_factor=1.5,
        description="조립체"
    ),
    "THRUST": LaborCost(
        part_type="THRUST",
        base_cost=120000,
        complexity_factor=1.4,
        description="스러스트 베어링"
    ),
    "COVER": LaborCost(
        part_type="COVER",
        base_cost=60000,
        complexity_factor=0.7,
        description="커버류"
    ),
    # ========== PANASIA BWMS 가공비 ==========
    "VALVE": LaborCost(
        part_type="VALVE",
        base_cost=180000,
        complexity_factor=1.5,
        description="BWMS 밸브류 (버터플라이, 글로브, 체크)"
    ),
    "PUMP": LaborCost(
        part_type="PUMP",
        base_cost=350000,
        complexity_factor=2.0,
        description="BWMS 펌프류 (원심, 자흡식)"
    ),
    "FILTER": LaborCost(
        part_type="FILTER",
        base_cost=250000,
        complexity_factor=1.8,
        description="BWMS 필터류 (자동역세척, 디스크)"
    ),
    "PIPE": LaborCost(
        part_type="PIPE",
        base_cost=45000,
        complexity_factor=0.6,
        description="BWMS 배관류"
    ),
    "FLANGE": LaborCost(
        part_type="FLANGE",
        base_cost=35000,
        complexity_factor=0.5,
        description="플랜지류"
    ),
    "UV_REACTOR": LaborCost(
        part_type="UV_REACTOR",
        base_cost=800000,
        complexity_factor=3.0,
        description="UV 반응기 (살균 장치)"
    ),
    "ELECTROLYZER": LaborCost(
        part_type="ELECTROLYZER",
        base_cost=650000,
        complexity_factor=2.8,
        description="전기분해조 (전해질 처리)"
    ),
    "TANK": LaborCost(
        part_type="TANK",
        base_cost=280000,
        complexity_factor=1.6,
        description="저장탱크류"
    ),
    "SENSOR": LaborCost(
        part_type="SENSOR",
        base_cost=120000,
        complexity_factor=1.2,
        description="센서류 (유량, 압력, 염도)"
    ),
    "CONTROL_PANEL": LaborCost(
        part_type="CONTROL_PANEL",
        base_cost=450000,
        complexity_factor=2.2,
        description="제어반/컨트롤 패널"
    ),
    "STRAINER": LaborCost(
        part_type="STRAINER",
        base_cost=85000,
        complexity_factor=0.9,
        description="스트레이너류"
    ),
    "HEAT_EXCHANGER": LaborCost(
        part_type="HEAT_EXCHANGER",
        base_cost=380000,
        complexity_factor=2.0,
        description="열교환기"
    ),
}


# 수량 할인 테이블
DEFAULT_QUANTITY_DISCOUNTS: List[Tuple[int, float]] = [
    (100, 0.15),  # 100개 이상: 15%
    (50, 0.10),   # 50개 이상: 10%
    (20, 0.07),   # 20개 이상: 7%
    (10, 0.05),   # 10개 이상: 5%
]


# 고객별 설정 (customer_config.py와 동기화)
DEFAULT_CUSTOMERS: Dict[str, CustomerConfig] = {
    "DSE": CustomerConfig(
        customer_id="DSE",
        customer_name="DSE Bearing",
        material_discount=0.05,  # 5% 재질 할인
        labor_discount=0.03,     # 3% 가공비 할인
        payment_terms=30
    ),
    "DOOSAN": CustomerConfig(
        customer_id="DOOSAN",
        customer_name="두산에너빌리티",
        material_discount=0.08,  # 8% 재질 할인
        labor_discount=0.05,     # 5% 가공비 할인
        payment_terms=45
    ),
    "KEPCO": CustomerConfig(
        customer_id="KEPCO",
        customer_name="한국전력공사",
        material_discount=0.10,  # 10% 대량구매 할인
        labor_discount=0.07,
        payment_terms=60
    ),
    "HYUNDAI": CustomerConfig(
        customer_id="HYUNDAI",
        customer_name="현대중공업",
        material_discount=0.07,
        labor_discount=0.05,
        payment_terms=30
    ),
    "SAMSUNG": CustomerConfig(
        customer_id="SAMSUNG",
        customer_name="삼성물산",
        material_discount=0.06,
        labor_discount=0.04,
        payment_terms=30,
        currency="USD"  # 해외 프로젝트
    ),
    "STX": CustomerConfig(
        customer_id="STX",
        customer_name="STX조선해양",
        material_discount=0.05,
        labor_discount=0.03,
        payment_terms=45
    ),
    "PANASIA": CustomerConfig(
        customer_id="PANASIA",
        customer_name="파나시아",
        material_discount=0.06,  # 6% BWMS 전문
        labor_discount=0.04,
        payment_terms=30
    ),
    "HANJIN": CustomerConfig(
        customer_id="HANJIN",
        customer_name="한진중공업",
        material_discount=0.05,
        labor_discount=0.03,
        payment_terms=30
    ),
}
