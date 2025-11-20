"""
Cost Estimator Module
제조 비용 산정 모듈
"""

from typing import Dict, List, Any


class CostEstimator:
    """제조 비용 산정 클래스"""

    def __init__(self):
        # 기본 단가 정의 (임시 값)
        self.base_rates = {
            "material": {
                "Mild Steel": 5.0,
                "Stainless Steel": 8.0,
                "Aluminum": 7.0,
                "Brass": 10.0,
                "default": 5.0
            },
            "process": {
                "TURNING": 20.0,
                "MILLING": 25.0,
                "DRILLING": 15.0,
                "GRINDING": 30.0,
                "default": 20.0
            }
        }

    def estimate_cost(
        self,
        manufacturing_processes: List[str],
        material: str,
        dimensions: List[str],
        gdt_count: int = 0,
        tolerance_count: int = 0,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        제조 비용 산정

        Args:
            manufacturing_processes: 제조 공정 리스트
            material: 재질
            dimensions: 치수 정보
            gdt_count: GD&T 개수
            tolerance_count: 공차 개수
            quantity: 수량

        Returns:
            비용 분석 결과
        """
        # 재료비 계산
        material_rate = self.base_rates["material"].get(
            material,
            self.base_rates["material"]["default"]
        )
        material_cost = material_rate * quantity

        # 가공비 계산
        process_cost = 0.0
        for process in manufacturing_processes:
            process_rate = self.base_rates["process"].get(
                process.upper(),
                self.base_rates["process"]["default"]
            )
            process_cost += process_rate

        process_cost *= quantity

        # 공차 추가 비용
        tolerance_cost = (gdt_count * 10.0 + tolerance_count * 5.0) * quantity

        # 총 비용
        subtotal = material_cost + process_cost + tolerance_cost
        tax = subtotal * 0.1  # 10% 세금
        total = subtotal + tax

        return {
            "material_cost": round(material_cost, 2),
            "process_cost": round(process_cost, 2),
            "tolerance_cost": round(tolerance_cost, 2),
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "unit_price": round(total / quantity, 2) if quantity > 0 else 0,
            "currency": "USD"
        }


def get_cost_estimator() -> CostEstimator:
    """Cost Estimator 인스턴스 반환"""
    return CostEstimator()
