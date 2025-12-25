"""
ImageInput Node Executor
워크플로우 시작점 - 업로드된 이미지를 다른 노드로 전달

2025-12-24: 기능 기반 재설계 (v2)
- drawing_type 파라미터 제거, features 체크박스만 사용
- features를 직접 파라미터로 받아 다음 노드로 전달
- BOM executor가 features를 세션에 저장
- 세션 UI가 features에 따라 동적으로 구성됨
"""
import logging
from typing import Dict, Any, Optional, List
from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)

# 기본 features (치수 도면 기준)
DEFAULT_FEATURES: List[str] = ["dimension_ocr", "dimension_verification", "gt_comparison"]


class ImageInputExecutor(BaseNodeExecutor):
    """ImageInput 실행기 - 전역 입력에서 이미지를 가져와 출력"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        전역 입력(context)에서 이미지를 가져와 출력으로 반환

        Returns:
            - image: Base64 인코딩된 이미지 문자열
            - features: 활성화된 기능 목록
        """
        # context는 이미 global_vars임 (pipeline_engine에서 context.global_vars를 전달)
        # 구조: {"inputs": {"image": "data:image/png;base64,..."}}
        initial_inputs = context.get("inputs", {})
        image_data = initial_inputs.get("image")

        if not image_data:
            raise ValueError("이미지 입력이 없습니다. 이미지를 먼저 업로드해주세요.")

        # features 파라미터 직접 가져오기 (2025-12-24 v2)
        features = self.parameters.get("features", DEFAULT_FEATURES)
        if not isinstance(features, list):
            features = DEFAULT_FEATURES
        logger.info(f"ImageInput - features: {features}")

        return {
            "image": image_data,
            "features": features,
            "message": f"Image loaded (size: {len(image_data)} chars, features: {len(features)})",
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # features가 리스트인지 확인
        features = self.parameters.get("features", DEFAULT_FEATURES)
        if not isinstance(features, list):
            return False, f"features는 리스트여야 합니다. 현재 타입: {type(features)}"
        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마 - 전역 입력에서 받으므로 빈 스키마"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 이미지"
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "활성화된 기능 목록"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("imageinput", ImageInputExecutor)
