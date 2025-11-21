"""
ImageInput Node Executor
워크플로우 시작점 - 업로드된 이미지를 다른 노드로 전달
"""
from typing import Dict, Any, Optional
from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry


class ImageInputExecutor(BaseNodeExecutor):
    """ImageInput 실행기 - 전역 입력에서 이미지를 가져와 출력"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        전역 입력(context)에서 이미지를 가져와 출력으로 반환

        Returns:
            - image: Base64 인코딩된 이미지 문자열
        """
        # context는 이미 global_vars임 (pipeline_engine에서 context.global_vars를 전달)
        # 구조: {"inputs": {"image": "data:image/png;base64,..."}}
        initial_inputs = context.get("inputs", {})
        image_data = initial_inputs.get("image")

        if not image_data:
            raise ValueError("이미지 입력이 없습니다. 이미지를 먼저 업로드해주세요.")

        return {
            "image": image_data,
            "message": f"Image loaded from workflow input (size: {len(image_data)} chars)",
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사 - ImageInput은 파라미터가 없음"""
        # ImageInput 노드는 파라미터가 없으므로 항상 유효
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
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("imageinput", ImageInputExecutor)
