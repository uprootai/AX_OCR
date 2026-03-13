"""
Price Database — PriceDatabase 클래스 + 싱글톤 팩토리
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import MaterialPrice, LaborCost, CustomerConfig
from .defaults import (
    DEFAULT_MATERIAL_PRICES,
    DEFAULT_LABOR_COSTS,
    DEFAULT_QUANTITY_DISCOUNTS,
    DEFAULT_CUSTOMERS,
)

logger = logging.getLogger(__name__)


class PriceDatabase:
    """가격 데이터베이스"""

    # 클래스 수준 기본값 참조 (하위 호환)
    DEFAULT_MATERIAL_PRICES = DEFAULT_MATERIAL_PRICES
    DEFAULT_LABOR_COSTS = DEFAULT_LABOR_COSTS
    DEFAULT_QUANTITY_DISCOUNTS = DEFAULT_QUANTITY_DISCOUNTS
    DEFAULT_CUSTOMERS = DEFAULT_CUSTOMERS

    def __init__(self, config_path: Optional[str] = None):
        """
        초기화

        Args:
            config_path: 외부 설정 파일 경로 (JSON)
        """
        self.material_prices = dict(DEFAULT_MATERIAL_PRICES)
        self.labor_costs = dict(DEFAULT_LABOR_COSTS)
        self.quantity_discounts = list(DEFAULT_QUANTITY_DISCOUNTS)
        self.customers = dict(DEFAULT_CUSTOMERS)

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
        """고객 설정 조회 (대소문자 무관)"""
        return self.customers.get(customer_id) or self.customers.get(customer_id.upper())

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
