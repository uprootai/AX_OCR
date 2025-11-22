"""
TextInput Node Executor
텍스트 입력 노드 - 사용자가 직접 입력한 텍스트를 다른 노드로 전달
"""
from typing import Dict, Any, Optional
from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry


class TextInputExecutor(BaseNodeExecutor):
    """TextInput 실행기 - 노드 파라미터에서 텍스트를 가져와 출력"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드 파라미터에서 텍스트 입력값을 가져와 출력으로 반환

        Parameters (from node config):
            - text (str): 사용자가 입력한 텍스트

        Returns:
            - text (str): 입력된 텍스트 문자열
            - length (int): 텍스트 길이
        """
        # 파라미터에서 텍스트 가져오기
        text_value = self.parameters.get("text", "")

        if not text_value:
            raise ValueError("텍스트 입력이 비어있습니다. 텍스트를 입력해주세요.")

        return {
            "text": text_value,
            "length": len(text_value),
            "message": f"Text input provided: {len(text_value)} characters",
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        text_value = self.parameters.get("text", "")

        if not text_value or not isinstance(text_value, str):
            return False, "텍스트 입력이 필요합니다 (text parameter)"

        if len(text_value) > 10000:
            return False, "텍스트가 너무 깁니다 (최대 10,000자)"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마 - 입력 노드이므로 빈 스키마"""
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
                "text": {
                    "type": "string",
                    "description": "사용자가 입력한 텍스트"
                },
                "length": {
                    "type": "integer",
                    "description": "텍스트 길이"
                }
            },
            "required": ["text"]
        }


# 실행기 등록
ExecutorRegistry.register("textinput", TextInputExecutor)
