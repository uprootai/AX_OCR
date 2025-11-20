"""
Base Node Executor
모든 노드 실행기의 추상 기반 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class BaseNodeExecutor(ABC):
    """노드 실행기 기본 클래스"""

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
        """
        Args:
            node_id: 노드 고유 ID
            node_type: 노드 타입
            parameters: 노드 파라미터
        """
        self.node_id = node_id
        self.node_type = node_type
        self.parameters = parameters
        self.logger = logging.getLogger(f"{__name__}.{node_type}")

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드 실행 (추상 메서드)

        Args:
            inputs: 입력 데이터
            context: 실행 컨텍스트 (전역 변수, 이전 노드 결과 등)

        Returns:
            실행 결과

        Raises:
            Exception: 실행 중 에러 발생 시
        """
        pass

    @abstractmethod
    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """
        파라미터 유효성 검사

        Returns:
            (is_valid, error_message)
        """
        pass

    async def run(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        실행 래퍼 (로깅, 타이밍, 에러 처리 포함)

        Args:
            inputs: 입력 데이터
            context: 실행 컨텍스트

        Returns:
            실행 결과 (메타데이터 포함)
        """
        start_time = time.time()
        self.logger.info(f"노드 {self.node_id} ({self.node_type}) 실행 시작")

        try:
            # 파라미터 유효성 검사
            is_valid, error = self.validate_parameters()
            if not is_valid:
                raise ValueError(f"파라미터 검증 실패: {error}")

            # 실제 실행
            result = await self.execute(inputs, context)

            execution_time = time.time() - start_time
            self.logger.info(
                f"노드 {self.node_id} 실행 완료 (소요 시간: {execution_time:.2f}초)"
            )

            # 메타데이터 추가
            return {
                "success": True,
                "node_id": self.node_id,
                "node_type": self.node_type,
                "data": result,
                "execution_time_ms": execution_time * 1000,
                "timestamp": time.time(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"노드 {self.node_id} 실행 실패: {str(e)}",
                exc_info=True
            )

            return {
                "success": False,
                "node_id": self.node_id,
                "node_type": self.node_type,
                "error": str(e),
                "execution_time_ms": execution_time * 1000,
                "timestamp": time.time(),
            }

    def get_input_schema(self) -> Dict[str, Any]:
        """
        입력 스키마 정의 (옵션)

        Returns:
            JSON Schema 형식의 입력 스키마
        """
        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """
        출력 스키마 정의 (옵션)

        Returns:
            JSON Schema 형식의 출력 스키마
        """
        return {"type": "object", "properties": {}}
