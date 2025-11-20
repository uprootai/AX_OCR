"""
SkinModel Node Executor
공차 예측 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from services import call_skinmodel_tolerance


class SkinmodelExecutor(BaseNodeExecutor):
    """SkinModel 공차 예측 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        SkinModel 공차 예측 실행

        Parameters:
            - dimensions: 차원 정보 리스트
            - material: 재료 정보 (default: {"name": "Steel"})
            - material_type: 재료 타입 (default: "steel")
            - manufacturing_process: 제조 공정 (default: "general")
            - correlation_length: 상관 길이 (default: 1.0)

        Returns:
            - tolerances: 공차 예측 결과
            - total_tolerances: 총 공차 개수
        """
        # 입력에서 차원 정보 가져오기
        dimensions = inputs.get("dimensions")

        if not dimensions:
            raise ValueError("dimensions 입력이 필요합니다")

        # 파라미터 추출
        material = self.parameters.get("material", {"name": "Steel"})
        material_type = self.parameters.get("material_type", "steel")
        manufacturing_process = self.parameters.get("manufacturing_process", "general")
        correlation_length = self.parameters.get("correlation_length", 1.0)

        # SkinModel API 호출
        result = await call_skinmodel_tolerance(
            dimensions=dimensions,
            material=material,
            material_type=material_type,
            manufacturing_process=manufacturing_process,
            correlation_length=correlation_length
        )

        return {
            "tolerances": result.get("data", {}).get("tolerances", []),
            "total_tolerances": len(result.get("data", {}).get("tolerances", [])),
            "model_used": result.get("model_used", "SkinModel"),
            "processing_time": result.get("processing_time", 0),
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # material 검증
        if "material" in self.parameters:
            material = self.parameters["material"]
            if not isinstance(material, dict):
                return False, "material은 딕셔너리여야 합니다"
            if "name" not in material:
                return False, "material에 'name' 키가 필요합니다"

        # material_type 검증
        if "material_type" in self.parameters:
            valid_types = ["steel", "aluminum", "plastic", "composite"]
            if self.parameters["material_type"] not in valid_types:
                return False, f"material_type은 {valid_types} 중 하나여야 합니다"

        # correlation_length 검증
        if "correlation_length" in self.parameters:
            cl = self.parameters["correlation_length"]
            if not isinstance(cl, (int, float)) or cl <= 0:
                return False, "correlation_length는 양수여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "dimensions": {
                    "type": "array",
                    "description": "차원 정보 리스트",
                    "items": {"type": "object"}
                }
            },
            "required": ["dimensions"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "tolerances": {
                    "type": "array",
                    "description": "공차 예측 결과"
                },
                "total_tolerances": {
                    "type": "integer",
                    "description": "총 공차 개수"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("skinmodel", SkinmodelExecutor)
