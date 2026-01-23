"""
Quote Generator Executor
BOM → 자동 견적 생성 (재료비, 가공비, 마진 계산)

가격 계산 방식:
1. 재료비: 재질별 단가 × 수량
2. 가공비: 부품 복잡도 × 기본 가공비
3. 마진: (재료비 + 가공비) × 마진율
4. 세금: (소계 + 마진) × 세율
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import re

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry


@dataclass
class QuoteLineItem:
    """견적 항목"""
    item_no: int
    part_no: str
    part_name: str
    material: str
    quantity: int
    unit_price: float
    material_cost: float
    labor_cost: float
    subtotal: float


@dataclass
class QuoteSummary:
    """견적 요약"""
    material_cost: float
    labor_cost: float
    subtotal: float
    material_markup: float
    labor_markup: float
    total_markup: float
    tax: float
    total: float
    currency: str
    item_count: int
    discount_applied: float = 0.0


@dataclass
class QuoteDocument:
    """견적서 문서"""
    quote_number: str
    date: str
    validity_date: str
    drawing_number: str
    title: str
    customer: str = ""
    notes: str = ""


class QuoteGeneratorExecutor(BaseNodeExecutor):
    """Quote Generator 실행기"""

    # 재질별 기본 단가 (KRW/kg) - 고객 제공 시 덮어쓰기 가능
    DEFAULT_MATERIAL_PRICES = {
        # 철강 계열
        "SF440A": 5000,
        "SF440": 5000,
        "SS400": 3500,
        "SM490A": 4500,
        "S45C": 4000,
        "S45C-N": 4200,
        "SCM440": 6000,
        # 스테인리스
        "SUS304": 12000,
        "SUS316": 18000,
        # 특수 합금
        "ASTM B23 GR.2": 45000,  # Babbitt
        "BABBITT": 45000,
        # 기본값
        "DEFAULT": 5000,
    }

    # 부품 유형별 기본 가공비 (KRW/개)
    DEFAULT_LABOR_COSTS = {
        "PAD": 50000,      # 패드류
        "RING": 30000,     # 링류
        "SEAL": 20000,     # 씰류
        "BEARING": 80000,  # 베어링
        "HOUSING": 100000, # 하우징
        "SHAFT": 70000,    # 축류
        "DEFAULT": 40000,  # 기본값
    }

    # 수량 할인율
    QUANTITY_DISCOUNTS = [
        (100, 0.15),  # 100개 이상 15% 할인
        (50, 0.10),   # 50개 이상 10% 할인
        (20, 0.07),   # 20개 이상 7% 할인
        (10, 0.05),   # 10개 이상 5% 할인
    ]

    # 통화별 기호
    CURRENCY_SYMBOLS = {
        "KRW": "₩",
        "USD": "$",
        "EUR": "€",
        "JPY": "¥",
    }

    def _get_material_price(self, material: str, pricing_table: Dict) -> float:
        """재질별 단가 조회"""
        # 커스텀 단가 테이블 우선
        if pricing_table and material.upper() in pricing_table:
            return pricing_table[material.upper()]

        # 기본 단가 테이블
        material_upper = material.upper().strip()
        for key, price in self.DEFAULT_MATERIAL_PRICES.items():
            if key in material_upper or material_upper in key:
                return price

        return self.DEFAULT_MATERIAL_PRICES["DEFAULT"]

    def _get_labor_cost(self, part_name: str) -> float:
        """부품 유형별 가공비 조회"""
        part_upper = part_name.upper()

        for key, cost in self.DEFAULT_LABOR_COSTS.items():
            if key in part_upper:
                return cost

        return self.DEFAULT_LABOR_COSTS["DEFAULT"]

    def _calculate_quantity_discount(self, quantity: int) -> float:
        """수량 할인율 계산"""
        for threshold, discount in self.QUANTITY_DISCOUNTS:
            if quantity >= threshold:
                return discount
        return 0.0

    def _generate_quote_number(self) -> str:
        """견적 번호 생성"""
        now = datetime.now()
        return f"Q-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

    def _estimate_weight(self, part_name: str, material: str) -> float:
        """부품 무게 추정 (kg) - 나중에 실제 데이터로 대체"""
        # 부품명 기반 무게 추정
        part_upper = part_name.upper()

        if "PAD" in part_upper:
            return 2.5
        elif "RING" in part_upper:
            return 1.5
        elif "SEAL" in part_upper:
            return 0.3
        elif "HOUSING" in part_upper:
            return 15.0
        elif "SHAFT" in part_upper:
            return 8.0
        elif "BEARING" in part_upper:
            return 5.0

        return 1.0  # 기본값

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quote Generator 실행

        Parameters:
            - bom: BOM 항목 목록
            - drawing_info: 도면 메타 정보
            - pricing_table: 커스텀 단가 테이블 (선택)
            - currency: 통화 단위
            - material_markup: 재료비 마진율 (%)
            - labor_markup: 가공비 마진율 (%)
            - tax_rate: 세율 (%)
            - include_tax: 세금 포함 여부
            - quantity_discount: 수량 할인 적용 여부
            - validity_days: 견적 유효 기간

        Returns:
            - quote: 견적서 문서
            - line_items: 견적 항목 목록
            - summary: 견적 요약
            - total_cost: 총 견적 금액
        """
        # 파라미터 추출
        currency = self.parameters.get("currency", "KRW")
        material_markup_rate = self.parameters.get("material_markup", 15) / 100
        labor_markup_rate = self.parameters.get("labor_markup", 20) / 100
        tax_rate = self.parameters.get("tax_rate", 10) / 100
        include_tax = self.parameters.get("include_tax", True)
        apply_quantity_discount = self.parameters.get("quantity_discount", True)
        validity_days = self.parameters.get("validity_days", 30)

        # 입력 데이터 추출
        bom = inputs.get("bom", [])
        drawing_info = inputs.get("drawing_info", {})
        pricing_table = inputs.get("pricing_table", {})

        # BOM 유효성 검사
        if not bom:
            return {
                "quote": None,
                "line_items": [],
                "summary": None,
                "total_cost": 0,
                "error": "BOM 데이터가 없습니다",
                "image": inputs.get("image", ""),
            }

        # 견적 항목 생성
        line_items: List[QuoteLineItem] = []
        total_material_cost = 0.0
        total_labor_cost = 0.0
        total_quantity = 0

        for item in bom:
            part_no = str(item.get("part_no", item.get("item_no", "")))
            part_name = item.get("part_name", "")
            material = item.get("material", "")
            quantity = item.get("quantity", 1)

            if not isinstance(quantity, int):
                try:
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    quantity = 1

            # 단가 계산
            material_price = self._get_material_price(material, pricing_table)
            weight = self._estimate_weight(part_name, material)
            unit_material_cost = material_price * weight

            # 가공비
            labor_cost_per_unit = self._get_labor_cost(part_name)

            # 수량 적용
            material_cost = unit_material_cost * quantity
            labor_cost = labor_cost_per_unit * quantity
            subtotal = material_cost + labor_cost

            line_item = QuoteLineItem(
                item_no=len(line_items) + 1,
                part_no=part_no,
                part_name=part_name,
                material=material,
                quantity=quantity,
                unit_price=unit_material_cost + labor_cost_per_unit,
                material_cost=material_cost,
                labor_cost=labor_cost,
                subtotal=subtotal,
            )
            line_items.append(line_item)

            total_material_cost += material_cost
            total_labor_cost += labor_cost
            total_quantity += quantity

        # 수량 할인 적용
        discount_rate = 0.0
        discount_amount = 0.0
        if apply_quantity_discount:
            discount_rate = self._calculate_quantity_discount(total_quantity)
            discount_amount = (total_material_cost + total_labor_cost) * discount_rate

        # 소계 (할인 적용)
        subtotal = total_material_cost + total_labor_cost - discount_amount

        # 마진 계산
        material_markup = total_material_cost * material_markup_rate
        labor_markup = total_labor_cost * labor_markup_rate
        total_markup = material_markup + labor_markup

        # 세금 계산
        taxable_amount = subtotal + total_markup
        tax_amount = taxable_amount * tax_rate if include_tax else 0

        # 총액
        total = taxable_amount + tax_amount

        # 견적서 문서 생성
        now = datetime.now()
        quote_doc = QuoteDocument(
            quote_number=self._generate_quote_number(),
            date=now.strftime("%Y-%m-%d"),
            validity_date=(now + timedelta(days=validity_days)).strftime("%Y-%m-%d"),
            drawing_number=drawing_info.get("drawing_number", ""),
            title=drawing_info.get("title", ""),
            customer=drawing_info.get("customer", ""),
            notes=f"견적 유효기간: {validity_days}일",
        )

        # 요약 생성
        summary = QuoteSummary(
            material_cost=round(total_material_cost),
            labor_cost=round(total_labor_cost),
            subtotal=round(subtotal),
            material_markup=round(material_markup),
            labor_markup=round(labor_markup),
            total_markup=round(total_markup),
            tax=round(tax_amount),
            total=round(total),
            currency=currency,
            item_count=len(line_items),
            discount_applied=round(discount_amount),
        )

        # 출력 생성
        output = {
            "quote": asdict(quote_doc),
            "line_items": [asdict(item) for item in line_items],
            "summary": asdict(summary),
            "material_cost": round(total_material_cost),
            "labor_cost": round(total_labor_cost),
            "total_cost": round(total),
            "quote_number": quote_doc.quote_number,
            "currency": currency,
            "currency_symbol": self.CURRENCY_SYMBOLS.get(currency, ""),
            # 설정값
            "markup_rates": {
                "material": material_markup_rate * 100,
                "labor": labor_markup_rate * 100,
            },
            "tax_rate": tax_rate * 100,
            "discount_rate": discount_rate * 100,
            # 원본 데이터 패스스루
            "bom": bom,
            "drawing_info": drawing_info,
            "image": inputs.get("image", ""),
        }

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # currency 검증
        if "currency" in self.parameters:
            currency = self.parameters["currency"]
            if currency not in ["KRW", "USD", "EUR", "JPY"]:
                return False, "currency는 KRW, USD, EUR, JPY 중 하나여야 합니다"

        # markup 검증
        for key in ["material_markup", "labor_markup"]:
            if key in self.parameters:
                value = self.parameters[key]
                if not (0 <= value <= 100):
                    return False, f"{key}는 0과 100 사이여야 합니다"

        # tax_rate 검증
        if "tax_rate" in self.parameters:
            rate = self.parameters["tax_rate"]
            if not (0 <= rate <= 30):
                return False, "tax_rate는 0과 30 사이여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "bom": {
                    "type": "array",
                    "description": "BOM 항목 목록"
                },
                "drawing_info": {
                    "type": "object",
                    "description": "도면 메타 정보"
                },
                "pricing_table": {
                    "type": "object",
                    "description": "커스텀 단가 테이블"
                }
            },
            "required": ["bom"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "quote": {
                    "type": "object",
                    "description": "견적서 문서"
                },
                "line_items": {
                    "type": "array",
                    "description": "견적 항목 목록"
                },
                "summary": {
                    "type": "object",
                    "description": "견적 요약"
                },
                "total_cost": {
                    "type": "number",
                    "description": "총 견적 금액"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("quotegenerator", QuoteGeneratorExecutor)
ExecutorRegistry.register("quote_generator", QuoteGeneratorExecutor)
ExecutorRegistry.register("quote", QuoteGeneratorExecutor)
