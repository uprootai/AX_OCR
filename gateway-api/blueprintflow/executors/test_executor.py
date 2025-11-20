"""
Test Node Executor
테스트용 더미 노드 실행기
"""
from typing import Dict, Any, Optional
import asyncio
from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry


class TestExecutor(BaseNodeExecutor):
    """테스트용 더미 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        간단한 테스트 실행 - 입력을 받아서 메시지를 추가하여 반환
        """
        # 파라미터에서 delay 가져오기 (초)
        delay = self.parameters.get("delay", 0.1)

        # 인위적인 지연 (실제 처리 시뮬레이션)
        await asyncio.sleep(delay)

        message = self.parameters.get("message", f"Hello from {self.node_id}")

        return {
            "node_id": self.node_id,
            "message": message,
            "inputs_received": inputs,
            "parameters": self.parameters,
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # delay가 있으면 숫자인지 확인
        if "delay" in self.parameters:
            try:
                float(self.parameters["delay"])
            except (ValueError, TypeError):
                return False, "delay 파라미터는 숫자여야 합니다"

        return True, None


# 실행기 등록
ExecutorRegistry.register("test", TestExecutor)
