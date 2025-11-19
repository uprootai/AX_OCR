"""
Tolerance Prediction and GD&T Validation Service
"""
import time
import logging
from typing import Dict, Any, List, Optional

from fastapi import HTTPException

try:
    from ml_predictor import get_ml_predictor
    ml_predictor = get_ml_predictor()
    logger = logging.getLogger(__name__)
    if ml_predictor:
        logger.info(f"ML Predictor initialized: {ml_predictor.is_available()}")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"ML Predictor not available: {e}")
    ml_predictor = None


class ToleranceService:
    """Service for tolerance prediction and GD&T validation"""

    def __init__(self):
        """Initialize tolerance service"""
        self.logger = logging.getLogger(__name__)
        self.ml_predictor = ml_predictor

    def predict_tolerances(
        self,
        dimensions: List,
        material,
        manufacturing_process: str,
        correlation_length: float
    ) -> Dict[str, Any]:
        """
        기하공차 예측 (ML-based with Rule-based fallback)

        ML 모델 우선 사용, 실패 시 Rule-based 휴리스틱 사용

        Args:
            dimensions: List of DimensionInput objects
            material: MaterialInput object
            manufacturing_process: Manufacturing process type
            correlation_length: Random Field correlation length

        Returns:
            Dictionary with predicted tolerances, manufacturability, and assemblability
        """
        try:
            self.logger.info(f"Predicting tolerances for {len(dimensions)} dimensions")
            self.logger.info(f"Material: {material.name}, Process: {manufacturing_process}")

            # 공통 변수 초기화
            max_dim = max([d.value for d in dimensions]) if dimensions else 100.0
            material_factors_map = {
                "Steel": 1.0,
                "Aluminum": 0.8,
                "Titanium": 1.5,
                "Plastic": 0.6
            }
            material_factor = material_factors_map.get(material.name, 1.0)
            size_factor = 1.0 + (max_dim / 1000.0) * 0.5

            # ML 모델 시도
            ml_predictions = None
            if self.ml_predictor and self.ml_predictor.is_available():
                try:
                    dims_dict = [{"type": d.type, "value": d.value} for d in dimensions]
                    mat_dict = {"name": material.name, "youngs_modulus": material.youngs_modulus}
                    ml_predictions = self.ml_predictor.predict(dims_dict, mat_dict, manufacturing_process)
                    if ml_predictions:
                        self.logger.info("✅ ML 모델 예측 사용")
                        flatness = ml_predictions["flatness"]
                        cylindricity = ml_predictions["cylindricity"]
                        position = ml_predictions["position"]
                        perpendicularity = ml_predictions["perpendicularity"]
                except Exception as e:
                    self.logger.warning(f"ML 예측 실패, Rule-based 사용: {e}")
                    ml_predictions = None

            # Rule-based fallback
            if ml_predictions is None:
                self.logger.info("⚠️  Rule-based 휴리스틱 사용")
                # 재질별 기본 공차 계수
                material_factors = {
                    "Steel": 1.0,
                    "Aluminum": 0.8,
                    "Titanium": 1.5,
                    "Plastic": 0.6
                }
                material_factor = material_factors.get(material.name, 1.0)

                # 제조 공정별 기본 공차
                process_tolerances = {
                    "machining": {"flatness": 0.02, "cylindricity": 0.03, "position": 0.025},
                    "casting": {"flatness": 0.15, "cylindricity": 0.20, "position": 0.15},
                    "3d_printing": {"flatness": 0.08, "cylindricity": 0.10, "position": 0.08}
                }
                base_tol = process_tolerances.get(manufacturing_process, process_tolerances["machining"])

                # 치수 크기에 따른 보정
                max_dim = max([d.value for d in dimensions]) if dimensions else 100.0
                size_factor = 1.0 + (max_dim / 1000.0) * 0.5

                # Correlation length 영향
                corr_factor = 1.0 + (correlation_length - 1.0) * 0.3

                # 최종 공차 계산
                flatness = round(base_tol["flatness"] * material_factor * size_factor * corr_factor, 4)
                cylindricity = round(base_tol["cylindricity"] * material_factor * size_factor * corr_factor, 4)
                position = round(base_tol["position"] * material_factor * size_factor * corr_factor, 4)
                perpendicularity = round(flatness * 0.7, 4)

            # 제조 가능성 평가
            avg_tolerance = (flatness + cylindricity + position) / 3
            if avg_tolerance < 0.05:
                difficulty = "Hard"
                score = 0.65
                recommendations = [
                    "Requires precision machining equipment",
                    "Consider CNC grinding for tight tolerances",
                    "Quality control critical - CMM inspection required"
                ]
            elif avg_tolerance < 0.10:
                difficulty = "Medium"
                score = 0.80
                recommendations = [
                    "Standard precision machining acceptable",
                    "Consider tighter fixturing for flatness control",
                    "Regular calibration of measuring equipment"
                ]
            else:
                difficulty = "Easy"
                score = 0.92
                recommendations = [
                    "Standard machining processes sufficient",
                    "Normal quality control procedures",
                    "Cost-effective manufacturing possible"
                ]

            # 조립성 평가 (작은 공차 = 더 좋은 조립성)
            assemblability_score = min(0.98, 0.70 + (0.1 - avg_tolerance) * 2)
            clearance = round(avg_tolerance * 3, 3)

            if avg_tolerance < 0.05:
                interference_risk = "Low"
            elif avg_tolerance < 0.15:
                interference_risk = "Medium"
            else:
                interference_risk = "High"

            # Simulate processing time
            time.sleep(0.5)

            result = {
                "predicted_tolerances": {
                    "flatness": flatness,
                    "cylindricity": cylindricity,
                    "position": position,
                    "perpendicularity": perpendicularity
                },
                "manufacturability": {
                    "score": round(score, 2),
                    "difficulty": difficulty,
                    "recommendations": recommendations
                },
                "assemblability": {
                    "score": round(assemblability_score, 2),
                    "clearance": clearance,
                    "interference_risk": interference_risk
                },
                "process_parameters": {
                    "correlation_length": correlation_length,
                    "material_factor": material_factor,
                    "size_factor": round(size_factor, 2),
                    "max_dimension": max_dim
                }
            }

            return result

        except Exception as e:
            self.logger.error(f"Tolerance prediction failed: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    def validate_gdt(
        self,
        dimensions: List,
        gdt_specs: Dict[str, float],
        material
    ) -> Dict[str, Any]:
        """
        GD&T 검증

        Args:
            dimensions: List of DimensionInput objects
            gdt_specs: GD&T specifications
            material: MaterialInput object

        Returns:
            Dictionary with validation results

        TODO: 실제 GDT Validator 연동
        """
        try:
            self.logger.info(f"Validating GD&T for {len(dimensions)} dimensions")
            self.logger.info(f"Specs: {gdt_specs}")

            # Simulate processing
            time.sleep(1.0)

            # Mock validation result
            result = {
                "validation_results": {
                    "flatness": {
                        "spec": gdt_specs.get("flatness", 0.05),
                        "predicted": 0.048,
                        "status": "PASS",
                        "margin": 0.002
                    },
                    "cylindricity": {
                        "spec": gdt_specs.get("cylindricity", 0.1),
                        "predicted": 0.092,
                        "status": "PASS",
                        "margin": 0.008
                    },
                    "position": {
                        "spec": gdt_specs.get("position", 0.08),
                        "predicted": 0.065,
                        "status": "PASS",
                        "margin": 0.015
                    }
                },
                "overall_status": "PASS",
                "pass_rate": 1.0,
                "recommendations": [
                    "All tolerances within specification",
                    "Consider process capability study (Cpk > 1.33)"
                ]
            }

            return result

        except Exception as e:
            self.logger.error(f"GDT validation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# Create singleton instance
tolerance_service = ToleranceService()
