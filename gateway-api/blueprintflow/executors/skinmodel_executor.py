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
            - dimensions: 차원 정보 리스트 (입력에서 받거나 수동 입력)
            - dimensions_manual: 수동 치수 입력 (JSON 문자열)
            - material: 재료 정보 (default: {"name": "Steel"})
            - material_type: 재료 타입 (default: "steel")
            - manufacturing_process: 제조 공정 (default: "general")
            - correlation_length: 상관 길이 (default: 1.0)

        Returns:
            - tolerances: 공차 예측 결과
            - total_tolerances: 총 공차 개수
        """
        import json
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔧 SkinModel 파라미터: {self.parameters}")
        logger.info(f"🔧 SkinModel 입력: {list(inputs.keys())}")

        # 입력에서 차원 정보 가져오기 (OCR 결과에서)
        dimensions = inputs.get("dimensions")

        # 다중 부모 노드인 경우 from_ 접두사로 된 입력에서 dimensions 찾기
        if not dimensions:
            for key, value in inputs.items():
                if key.startswith("from_") and isinstance(value, dict):
                    if "dimensions" in value and value["dimensions"]:
                        dimensions = value["dimensions"]
                        logger.info(f"🔧 {key}에서 dimensions 발견: {len(dimensions)}개")
                        break

        # 입력이 없으면 수동 입력 파라미터 확인
        if not dimensions:
            dimensions_manual = self.parameters.get("dimensions_manual", "")
            logger.info(f"🔧 dimensions_manual 값: '{dimensions_manual}'")
            if dimensions_manual and dimensions_manual.strip():
                try:
                    dimensions = json.loads(dimensions_manual)
                    logger.info(f"🔧 파싱된 dimensions: {dimensions}")
                except json.JSONDecodeError as e:
                    raise ValueError(f"dimensions_manual JSON 파싱 오류: {e}. 예시: [{{'nominal': 50, 'tolerance': 0.1}}]")

        if not dimensions:
            raise ValueError("dimensions 입력이 필요합니다. OCR 노드를 연결하거나 'dimensions_manual' 파라미터에 JSON을 입력하세요. 예: [{\"value\": 50, \"tolerance\": 0.1, \"type\": \"length\"}]")

        # 파라미터 추출
        material = self.parameters.get("material", "steel")  # 문자열 또는 객체
        material_type = self.parameters.get("material_type", "steel")
        manufacturing_process = self.parameters.get("manufacturing_process", "machining")
        correlation_length = self.parameters.get("correlation_length", 1.0)

        # SkinModel API 호출
        result = await call_skinmodel_tolerance(
            dimensions=dimensions,
            material=material,
            material_type=material_type,
            manufacturing_process=manufacturing_process,
            correlation_length=correlation_length
        )

        data = result.get("data", {})
        predicted_tolerances = data.get("predicted_tolerances", {})
        manufacturability = data.get("manufacturability", {})

        output = {
            "predicted_tolerances": predicted_tolerances,
            "manufacturability_score": manufacturability.get("score", 0),
            "difficulty": manufacturability.get("difficulty", "Unknown"),
            "recommendations": manufacturability.get("recommendations", []),
            "assemblability": data.get("assemblability", {}),
            "processing_time": result.get("processing_time", 0),
        }

        # 원본 이미지 패스스루 (후속 노드에서 필요)
        if inputs.get("image"):
            output["image"] = inputs["image"]

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        return output

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
                "predicted_tolerances": {
                    "type": "object",
                    "description": "예측된 GD&T 공차 (flatness, cylindricity, position, perpendicularity)"
                },
                "manufacturability_score": {
                    "type": "number",
                    "description": "제조 가능성 점수 (0-1)"
                },
                "difficulty": {
                    "type": "string",
                    "description": "제조 난이도 (Easy, Medium, Hard)"
                },
                "recommendations": {
                    "type": "array",
                    "description": "제조 권장 사항"
                },
                "assemblability": {
                    "type": "object",
                    "description": "조립성 분석 결과"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("skinmodel", SkinmodelExecutor)
