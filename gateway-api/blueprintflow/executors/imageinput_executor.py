"""
ImageInput Node Executor
워크플로우 시작점 - 업로드된 이미지를 다른 노드로 전달

2025-12-22: drawing_type 파라미터 출력 추가
- BOM executor가 drawing_type을 받아 세션에 저장
- WorkflowPage가 drawing_type에 따라 UI 조정
"""
import logging
from typing import Dict, Any, Optional
from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


class ImageInputExecutor(BaseNodeExecutor):
    """ImageInput 실행기 - 전역 입력에서 이미지를 가져와 출력"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        전역 입력(context)에서 이미지를 가져와 출력으로 반환

        Returns:
            - image: Base64 인코딩된 이미지 문자열
            - drawing_type: 선택된 도면 타입 (dimension, electrical_panel, pid, assembly 등)
        """
        # context는 이미 global_vars임 (pipeline_engine에서 context.global_vars를 전달)
        # 구조: {"inputs": {"image": "data:image/png;base64,..."}}
        initial_inputs = context.get("inputs", {})
        image_data = initial_inputs.get("image")

        if not image_data:
            raise ValueError("이미지 입력이 없습니다. 이미지를 먼저 업로드해주세요.")

        # drawing_type 파라미터 가져오기 (2025-12-22)
        # parameters는 BaseNodeExecutor에서 self.parameters로 접근
        drawing_type = self.parameters.get("drawing_type", "dimension")
        logger.info(f"ImageInput - drawing_type: {drawing_type}")

        return {
            "image": image_data,
            "drawing_type": drawing_type,
            "message": f"Image loaded (size: {len(image_data)} chars, type: {drawing_type})",
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # drawing_type이 유효한 값인지 확인
        valid_types = [
            "dimension", "electrical_panel", "pid", "assembly",
            "dimension_bom", "electrical_circuit", "architectural", "auto"
        ]
        drawing_type = self.parameters.get("drawing_type", "dimension")
        if drawing_type not in valid_types:
            return False, f"유효하지 않은 도면 타입: {drawing_type}. 가능한 값: {valid_types}"
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
                "drawing_type": {
                    "type": "string",
                    "description": "선택된 도면 타입",
                    "enum": ["dimension", "electrical_panel", "pid", "assembly",
                             "dimension_bom", "electrical_circuit", "architectural", "auto"]
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("imageinput", ImageInputExecutor)
