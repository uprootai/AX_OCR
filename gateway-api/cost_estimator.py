"""
비용 산정 엔진

제조 공정, 재질, 치수 정보를 기반으로 제조 비용 및 리드타임 추정
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessType(Enum):
    """제조 공정 타입"""
    TURNING = "Turning"
    MILLING = "Milling"
    DRILLING = "Drilling"
    BORING = "Boring"
    REAMING = "Reaming"
    GRINDING = "Grinding"
    DEBURRING = "Deburring"
    WELDING = "Welding"
    CASTING = "Casting"
    FORGING = "Forging"
    HEAT_TREATMENT = "Heat Treatment"
    SURFACE_TREATMENT = "Surface Treatment"
    INSPECTION = "Inspection"


class MaterialType(Enum):
    """재질 타입"""
    # 강철류
    STEEL_MILD = "Mild Steel"
    STEEL_CARBON = "Carbon Steel"
    STEEL_STAINLESS_304 = "STS304"
    STEEL_STAINLESS_316 = "STS316"
    STEEL_ALLOY = "Alloy Steel"

    # 알루미늄
    ALUMINUM_6061 = "AL6061"
    ALUMINUM_7075 = "AL7075"

    # 기타
    BRASS = "Brass"
    COPPER = "Copper"
    TITANIUM = "Titanium"
    PLASTIC = "Plastic"


@dataclass
class ProcessCostData:
    """공정별 비용 데이터"""
    hourly_rate: float  # USD/hour
    setup_time: float   # hours
    unit_time: float    # hours per unit
    description: str


@dataclass
class MaterialCostData:
    """재질별 비용 데이터"""
    cost_per_kg: float  # USD/kg
    density: float      # kg/m³
    machinability_factor: float  # 1.0 = normal, >1.0 = harder to machine


# 공정별 기본 비용 데이터베이스
PROCESS_COST_DB: Dict[str, ProcessCostData] = {
    "Turning": ProcessCostData(
        hourly_rate=45.0,
        setup_time=0.5,
        unit_time=0.3,
        description="Lathe machining for cylindrical parts"
    ),
    "Milling": ProcessCostData(
        hourly_rate=55.0,
        setup_time=0.8,
        unit_time=0.5,
        description="CNC milling for complex surfaces"
    ),
    "Drilling": ProcessCostData(
        hourly_rate=40.0,
        setup_time=0.3,
        unit_time=0.2,
        description="Hole drilling operations"
    ),
    "Boring": ProcessCostData(
        hourly_rate=50.0,
        setup_time=0.4,
        unit_time=0.3,
        description="Precision hole finishing"
    ),
    "Reaming": ProcessCostData(
        hourly_rate=42.0,
        setup_time=0.2,
        unit_time=0.15,
        description="Precision hole sizing"
    ),
    "Grinding": ProcessCostData(
        hourly_rate=60.0,
        setup_time=1.0,
        unit_time=0.4,
        description="Precision surface finishing"
    ),
    "Deburring": ProcessCostData(
        hourly_rate=35.0,
        setup_time=0.1,
        unit_time=0.1,
        description="Edge finishing and burr removal"
    ),
    "Welding": ProcessCostData(
        hourly_rate=65.0,
        setup_time=0.5,
        unit_time=0.4,
        description="Material joining processes"
    ),
    "Casting": ProcessCostData(
        hourly_rate=80.0,
        setup_time=10.0,
        unit_time=0.2,
        description="Metal casting processes"
    ),
    "Forging": ProcessCostData(
        hourly_rate=70.0,
        setup_time=5.0,
        unit_time=0.3,
        description="Metal forming by compression"
    ),
    "Heat Treatment": ProcessCostData(
        hourly_rate=50.0,
        setup_time=1.0,
        unit_time=2.0,
        description="Thermal processing for material properties"
    ),
    "Surface Treatment": ProcessCostData(
        hourly_rate=45.0,
        setup_time=0.5,
        unit_time=0.3,
        description="Surface coating and finishing"
    ),
    "Inspection": ProcessCostData(
        hourly_rate=55.0,
        setup_time=0.3,
        unit_time=0.5,
        description="Quality control and measurement"
    ),
}


# 재질별 비용 데이터베이스
MATERIAL_COST_DB: Dict[str, MaterialCostData] = {
    "Mild Steel": MaterialCostData(cost_per_kg=2.0, density=7850, machinability_factor=1.0),
    "Carbon Steel": MaterialCostData(cost_per_kg=2.5, density=7850, machinability_factor=1.1),
    "STS304": MaterialCostData(cost_per_kg=8.0, density=8000, machinability_factor=1.5),
    "STS316": MaterialCostData(cost_per_kg=10.0, density=8000, machinability_factor=1.6),
    "Alloy Steel": MaterialCostData(cost_per_kg=5.0, density=7850, machinability_factor=1.3),
    "AL6061": MaterialCostData(cost_per_kg=4.0, density=2700, machinability_factor=0.7),
    "AL7075": MaterialCostData(cost_per_kg=6.0, density=2810, machinability_factor=0.8),
    "Brass": MaterialCostData(cost_per_kg=7.0, density=8500, machinability_factor=0.9),
    "Copper": MaterialCostData(cost_per_kg=9.0, density=8960, machinability_factor=1.0),
    "Titanium": MaterialCostData(cost_per_kg=25.0, density=4500, machinability_factor=2.5),
    "Plastic": MaterialCostData(cost_per_kg=3.0, density=1200, machinability_factor=0.5),
}


def normalize_material_name(material: str) -> str:
    """재질명 정규화"""
    material = material.strip().upper()

    # 매핑 테이블
    material_mapping = {
        "STS304": "STS304",
        "SS304": "STS304",
        "304": "STS304",
        "STAINLESS 304": "STS304",
        "STS316": "STS316",
        "SS316": "STS316",
        "316": "STS316",
        "AL6061": "AL6061",
        "ALUMINUM 6061": "AL6061",
        "6061": "AL6061",
        "AL7075": "AL7075",
        "ALUMINUM 7075": "AL7075",
        "7075": "AL7075",
        "MILD STEEL": "Mild Steel",
        "CARBON STEEL": "Carbon Steel",
        "SM45C": "Carbon Steel",
        "S45C": "Carbon Steel",
    }

    return material_mapping.get(material, "Mild Steel")


def estimate_volume(dimensions: List[str]) -> float:
    """
    치수 정보로부터 대략적인 부피 추정 (mm³)

    간단한 휴리스틱:
    - φ로 시작하는 직경 치수에서 가장 큰 값 찾기
    - 선형 치수에서 길이 찾기
    - 원통 또는 직육면체로 근사
    """
    try:
        diameters = []
        lengths = []

        for dim in dimensions:
            # φ 기호 처리
            if 'φ' in dim or 'Ø' in dim or 'ø' in dim:
                # 숫자 추출
                import re
                numbers = re.findall(r'\d+\.?\d*', dim)
                if numbers:
                    diameters.append(float(numbers[0]))
            else:
                # 단순 숫자
                import re
                numbers = re.findall(r'\d+\.?\d*', dim)
                if numbers:
                    val = float(numbers[0])
                    if val > 10:  # 10mm 이상은 길이로 간주
                        lengths.append(val)

        # 부피 계산
        if diameters and lengths:
            # 원통 근사: V = π * r² * h
            max_diameter = max(diameters)
            max_length = max(lengths)
            radius = max_diameter / 2
            volume = 3.14159 * (radius ** 2) * max_length
        elif diameters:
            # 구 근사: V = 4/3 * π * r³
            max_diameter = max(diameters)
            radius = max_diameter / 2
            volume = (4/3) * 3.14159 * (radius ** 3)
        elif len(lengths) >= 3:
            # 직육면체 근사: V = l * w * h
            sorted_lengths = sorted(lengths, reverse=True)
            volume = sorted_lengths[0] * sorted_lengths[1] * sorted_lengths[2]
        else:
            # 기본값: 100 x 100 x 100 mm
            volume = 100 * 100 * 100

        return volume

    except Exception as e:
        logger.warning(f"Volume estimation failed: {e}, using default")
        return 100 * 100 * 100  # 기본값 1000 cm³


def estimate_complexity_factor(
    dimensions: List[str],
    gdt_count: int,
    tolerance_count: int
) -> float:
    """
    복잡도 계수 추정

    Returns:
        1.0 = 기본, >1.0 = 더 복잡 (시간 증가)
    """
    base_factor = 1.0

    # 치수 개수에 따른 복잡도
    if len(dimensions) > 20:
        base_factor += 0.3
    elif len(dimensions) > 10:
        base_factor += 0.15

    # GD&T 개수에 따른 복잡도
    if gdt_count > 5:
        base_factor += 0.3
    elif gdt_count > 0:
        base_factor += 0.15

    # 공차 개수에 따른 복잡도
    if tolerance_count > 10:
        base_factor += 0.2
    elif tolerance_count > 5:
        base_factor += 0.1

    return base_factor


class CostEstimator:
    """비용 산정 엔진"""

    def __init__(
        self,
        process_cost_db: Dict[str, ProcessCostData] = None,
        material_cost_db: Dict[str, MaterialCostData] = None
    ):
        self.process_cost_db = process_cost_db or PROCESS_COST_DB
        self.material_cost_db = material_cost_db or MATERIAL_COST_DB

    def estimate_cost(
        self,
        manufacturing_processes: Dict[str, str],
        material: str,
        dimensions: List[str],
        gdt_count: int = 0,
        tolerance_count: int = 0,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        제조 비용 추정

        Args:
            manufacturing_processes: VL 모델이 추론한 제조 공정 딕셔너리
            material: 재질명
            dimensions: 치수 리스트
            gdt_count: GD&T 개수
            tolerance_count: 공차 개수
            quantity: 생산 수량

        Returns:
            {
                "material_cost": float,
                "process_costs": [{"name": str, "cost": float, "time": float}, ...],
                "total_process_cost": float,
                "setup_cost": float,
                "unit_cost": float,
                "total_cost": float,
                "lead_time_days": float,
                "breakdown": {...}
            }
        """
        try:
            # 재질 정규화
            normalized_material = normalize_material_name(material)
            material_data = self.material_cost_db.get(normalized_material)

            if not material_data:
                logger.warning(f"Material {material} not found, using Mild Steel")
                material_data = self.material_cost_db["Mild Steel"]

            # 부피 추정 (mm³)
            volume_mm3 = estimate_volume(dimensions)
            volume_m3 = volume_mm3 / 1e9

            # 질량 추정 (kg)
            mass_kg = volume_m3 * material_data.density

            # 재료비
            material_cost = mass_kg * material_data.cost_per_kg

            # 복잡도 계수
            complexity = estimate_complexity_factor(dimensions, gdt_count, tolerance_count)

            # 공정별 비용 계산
            process_costs = []
            total_setup_time = 0
            total_unit_time = 0

            for process_name in manufacturing_processes.keys():
                process_data = self.process_cost_db.get(process_name)

                if not process_data:
                    logger.warning(f"Process {process_name} not found in cost DB")
                    continue

                # 가공성 및 복잡도 반영
                adjusted_unit_time = (
                    process_data.unit_time *
                    material_data.machinability_factor *
                    complexity
                )

                setup_cost = process_data.setup_time * process_data.hourly_rate
                unit_cost = adjusted_unit_time * process_data.hourly_rate

                process_costs.append({
                    "name": process_name,
                    "description": process_data.description,
                    "setup_cost": round(setup_cost, 2),
                    "unit_cost": round(unit_cost, 2),
                    "setup_time_hours": round(process_data.setup_time, 2),
                    "unit_time_hours": round(adjusted_unit_time, 2),
                    "hourly_rate": process_data.hourly_rate
                })

                total_setup_time += process_data.setup_time
                total_unit_time += adjusted_unit_time

            # 총 비용 계산
            total_setup_cost = sum(p["setup_cost"] for p in process_costs)
            total_unit_process_cost = sum(p["unit_cost"] for p in process_costs)
            unit_cost = material_cost + total_unit_process_cost
            total_cost = total_setup_cost + (unit_cost * quantity)

            # 리드타임 추정 (일)
            # 가정: 하루 8시간 작업, 병렬 처리 불가
            total_time_hours = total_setup_time + (total_unit_time * quantity)
            lead_time_days = (total_time_hours / 8) * 1.5  # 1.5x 버퍼

            result = {
                "status": "success",
                "material_cost_per_unit": round(material_cost, 2),
                "process_costs": process_costs,
                "total_setup_cost": round(total_setup_cost, 2),
                "unit_cost": round(unit_cost, 2),
                "total_cost": round(total_cost, 2),
                "quantity": quantity,
                "lead_time_days": round(lead_time_days, 1),
                "breakdown": {
                    "material": normalized_material,
                    "mass_kg": round(mass_kg, 3),
                    "volume_cm3": round(volume_mm3 / 1000, 1),
                    "complexity_factor": round(complexity, 2),
                    "total_setup_time_hours": round(total_setup_time, 2),
                    "total_unit_time_hours": round(total_unit_time, 2)
                }
            }

            logger.info(f"Cost estimation completed: ${total_cost:.2f}, {lead_time_days:.1f} days")
            return result

        except Exception as e:
            logger.error(f"Cost estimation failed: {e}")
            raise ValueError(f"Cost estimation error: {str(e)}")


# 싱글톤 인스턴스
_cost_estimator_instance = None


def get_cost_estimator() -> CostEstimator:
    """CostEstimator 싱글톤 인스턴스 반환"""
    global _cost_estimator_instance
    if _cost_estimator_instance is None:
        _cost_estimator_instance = CostEstimator()
    return _cost_estimator_instance
