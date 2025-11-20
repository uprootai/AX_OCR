"""
Loop Node Executor
반복 처리 제어 노드 (Phase 2 간단 버전)
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry


class LoopExecutor(BaseNodeExecutor):
    """Loop 반복 처리 실행기 (간단 버전)"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        반복 처리 (Phase 2에서는 단순 구현)

        Parameters:
            - array_field: 반복할 배열 필드 이름
            - max_iterations: 최대 반복 횟수 (default: 100)

        Returns:
            - iterations: 실행된 반복 횟수
            - items: 반복 대상 아이템 목록
            - message: 상태 메시지

        Note:
            Phase 3에서 실제 반복 실행 로직 구현 예정
            현재는 메타데이터만 반환
        """
        array_field = self.parameters.get("array_field", "items")
        max_iterations = self.parameters.get("max_iterations", 100)

        # 입력에서 배열 필드 가져오기
        items = inputs.get(array_field, [])

        if not isinstance(items, list):
            self.logger.warning(f"{array_field}가 배열이 아닙니다: {type(items)}")
            items = []

        iteration_count = min(len(items), max_iterations)

        self.logger.info(f"Loop: {iteration_count}개 아이템 처리 예정")

        return {
            "iterations": iteration_count,
            "items": items[:max_iterations],
            "array_field": array_field,
            "max_iterations": max_iterations,
            "message": f"Phase 2: Loop 메타데이터 반환 (실제 반복은 Phase 3에서 구현)",
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        if "max_iterations" in self.parameters:
            max_iter = self.parameters["max_iterations"]
            if not isinstance(max_iter, int) or max_iter <= 0:
                return False, "max_iterations는 양의 정수여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "description": "배열 필드를 포함한 입력 데이터"
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "iterations": {
                    "type": "integer",
                    "description": "실행된 반복 횟수"
                },
                "items": {
                    "type": "array",
                    "description": "처리된 아이템 목록"
                },
                "message": {
                    "type": "string",
                    "description": "상태 메시지"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("loop", LoopExecutor)
