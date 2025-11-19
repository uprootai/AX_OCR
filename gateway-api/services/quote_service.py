"""
Quote Service

Manufacturing quote calculation
"""
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def calculate_quote(
    ocr_data: Dict,
    tolerance_data: Dict,
    material_cost_per_kg: float,
    machining_rate_per_hour: float,
    tolerance_premium_factor: float
) -> Dict[str, Any]:
    """
    견적 계산

    Args:
        ocr_data: OCR 추출 데이터
        tolerance_data: 공차 분석 데이터
        material_cost_per_kg: 재료 단가 (USD/kg)
        machining_rate_per_hour: 가공 시간당 비용 (USD/hour)
        tolerance_premium_factor: 공차 정밀도 비용 계수

    Returns:
        견적 정보 dict
    """
    try:
        # Mock 계산 (실제 구현 시 도메인 로직으로 대체)
        dimensions = ocr_data.get("data", {}).get("dimensions", [])
        manufacturability = tolerance_data.get("data", {}).get("manufacturability", {})

        # 재료비 추정 (간단한 체적 계산)
        estimated_volume = 0.05  # m³ (Mock)
        material_density = 7850  # kg/m³ (Steel)
        material_weight = estimated_volume * material_density
        material_cost = material_weight * material_cost_per_kg

        # 가공비 추정
        difficulty_multiplier = {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.5
        }.get(manufacturability.get("difficulty", "Medium"), 1.5)

        estimated_machining_hours = 20.0 * difficulty_multiplier
        machining_cost = estimated_machining_hours * machining_rate_per_hour

        # 공차 프리미엄
        num_tight_tolerances = len([d for d in dimensions if d.get("tolerance")])
        tolerance_premium = num_tight_tolerances * 100 * tolerance_premium_factor

        total_cost = material_cost + machining_cost + tolerance_premium

        return {
            "quote_id": f"Q{int(time.time())}",
            "breakdown": {
                "material_cost": round(material_cost, 2),
                "machining_cost": round(machining_cost, 2),
                "tolerance_premium": round(tolerance_premium, 2),
                "total": round(total_cost, 2)
            },
            "details": {
                "material_weight_kg": round(material_weight, 2),
                "estimated_machining_hours": round(estimated_machining_hours, 1),
                "num_tight_tolerances": num_tight_tolerances,
                "difficulty": manufacturability.get("difficulty", "Medium")
            },
            "lead_time_days": 15,
            "confidence": 0.85
        }

    except Exception as e:
        logger.error(f"Quote calculation failed: {e}")
        return {"error": str(e)}
