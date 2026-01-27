"""
DSE Bearing Price Database Service

재질별 단가, 가공비, 할인율 관리
외부 JSON 파일에서 가격 데이터 로드 지원
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


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


class PriceDatabase:
    """가격 데이터베이스"""

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

    def __init__(self, config_path: Optional[str] = None):
        """
        초기화

        Args:
            config_path: 외부 설정 파일 경로 (JSON)
        """
        self.material_prices = dict(self.DEFAULT_MATERIAL_PRICES)
        self.labor_costs = dict(self.DEFAULT_LABOR_COSTS)
        self.quantity_discounts = list(self.DEFAULT_QUANTITY_DISCOUNTS)
        self.customers = dict(self.DEFAULT_CUSTOMERS)

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> bool:
        """외부 JSON 설정 파일 로드"""
        try:
            path = Path(config_path)
            if not path.exists():
                logger.warning(f"설정 파일 없음: {config_path}")
                return False

            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 재질 가격 로드
            if "material_prices" in config:
                for code, data in config["material_prices"].items():
                    self.material_prices[code] = MaterialPrice(**data)

            # 가공비 로드
            if "labor_costs" in config:
                for part_type, data in config["labor_costs"].items():
                    self.labor_costs[part_type] = LaborCost(**data)

            # 수량 할인 로드
            if "quantity_discounts" in config:
                self.quantity_discounts = [
                    (d["min_qty"], d["discount"])
                    for d in config["quantity_discounts"]
                ]

            # 고객 설정 로드
            if "customers" in config:
                for customer_id, data in config["customers"].items():
                    self.customers[customer_id] = CustomerConfig(**data)

            logger.info(f"가격 설정 로드 완료: {config_path}")
            return True

        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return False

    def get_material_price(self, material: str, customer_id: Optional[str] = None) -> float:
        """
        재질별 단가 조회

        Args:
            material: 재질 코드
            customer_id: 고객 ID (할인 적용)

        Returns:
            단가 (KRW/kg)
        """
        material_upper = material.upper().strip()

        # 정확한 매칭
        if material_upper in self.material_prices:
            price = self.material_prices[material_upper].price_per_kg
        else:
            # 부분 매칭
            price = 5000  # 기본값
            for code, mat_price in self.material_prices.items():
                if code in material_upper or material_upper in code:
                    price = mat_price.price_per_kg
                    break

        # 고객 할인 적용
        if customer_id and customer_id in self.customers:
            discount = self.customers[customer_id].material_discount
            price = price * (1 - discount)

        return price

    def get_labor_cost(self, description: str, customer_id: Optional[str] = None) -> float:
        """
        부품 타입별 가공비 조회

        Args:
            description: 부품 설명
            customer_id: 고객 ID (할인 적용)

        Returns:
            가공비 (KRW)
        """
        desc_upper = description.upper()
        cost = 30000  # 기본값

        for part_type, labor in self.labor_costs.items():
            if part_type in desc_upper:
                cost = labor.base_cost * labor.complexity_factor
                break

        # 고객 할인 적용
        if customer_id and customer_id in self.customers:
            discount = self.customers[customer_id].labor_discount
            cost = cost * (1 - discount)

        return cost

    def get_quantity_discount(self, total_qty: int) -> float:
        """
        수량 할인율 계산

        Args:
            total_qty: 총 수량

        Returns:
            할인율 (0.0 ~ 1.0)
        """
        for min_qty, discount in sorted(self.quantity_discounts, reverse=True):
            if total_qty >= min_qty:
                return discount
        return 0.0

    def get_customer_config(self, customer_id: str) -> Optional[CustomerConfig]:
        """고객 설정 조회"""
        return self.customers.get(customer_id)

    def list_materials(self) -> List[Dict[str, Any]]:
        """모든 재질 목록 반환"""
        return [
            {
                "code": mat.code,
                "name_kr": mat.name_kr,
                "name_en": mat.name_en,
                "price_per_kg": mat.price_per_kg,
                "category": mat.category
            }
            for mat in self.material_prices.values()
        ]

    def list_labor_costs(self) -> List[Dict[str, Any]]:
        """모든 가공비 목록 반환"""
        return [
            {
                "part_type": labor.part_type,
                "base_cost": labor.base_cost,
                "complexity_factor": labor.complexity_factor,
                "description": labor.description
            }
            for labor in self.labor_costs.values()
        ]

    def calculate_quote(
        self,
        parts: List[Dict[str, Any]],
        customer_id: Optional[str] = None,
        material_markup: float = 1.3,
        labor_markup: float = 1.5,
        tax_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        BOM 데이터로 견적 계산

        Args:
            parts: 부품 리스트 [{"description": ..., "material": ..., "qty": ..., "weight": ...}, ...]
            customer_id: 고객 ID
            material_markup: 재질 마크업
            labor_markup: 가공비 마크업
            tax_rate: 세율

        Returns:
            견적 데이터
        """
        line_items = []
        total_qty = sum(p.get("qty", 1) for p in parts)
        qty_discount = self.get_quantity_discount(total_qty)

        for part in parts:
            description = part.get("description", "")
            material = part.get("material", "DEFAULT")
            qty = part.get("qty", 1)
            weight = part.get("weight", 1.0)  # kg

            # 단가 계산
            mat_price = self.get_material_price(material, customer_id)
            material_cost = weight * mat_price * material_markup

            labor_cost = self.get_labor_cost(description, customer_id) * labor_markup

            unit_price = material_cost + labor_cost
            total_price = unit_price * qty

            line_items.append({
                "no": part.get("no", ""),
                "description": description,
                "material": material,
                "qty": qty,
                "weight": weight,
                "material_cost": round(material_cost, 0),
                "labor_cost": round(labor_cost, 0),
                "unit_price": round(unit_price, 0),
                "total_price": round(total_price, 0)
            })

        subtotal = sum(item["total_price"] for item in line_items)
        discount_amount = subtotal * qty_discount
        tax = (subtotal - discount_amount) * tax_rate
        total = subtotal - discount_amount + tax

        return {
            "line_items": line_items,
            "subtotal": round(subtotal, 0),
            "quantity_discount_rate": qty_discount,
            "discount_amount": round(discount_amount, 0),
            "tax_rate": tax_rate,
            "tax": round(tax, 0),
            "total": round(total, 0),
            "customer_id": customer_id,
            "currency": self.customers[customer_id].currency if customer_id and customer_id in self.customers else "KRW"
        }


# 싱글톤 인스턴스
_price_db_instance = None


def get_price_database(config_path: Optional[str] = None) -> PriceDatabase:
    """가격 데이터베이스 인스턴스 반환"""
    global _price_db_instance
    if _price_db_instance is None:
        _price_db_instance = PriceDatabase(config_path)
    return _price_db_instance
