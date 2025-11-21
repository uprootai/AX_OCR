"""
Executor Registry
노드 실행기 팩토리 및 레지스트리
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExecutorRegistry:
    """노드 실행기 레지스트리"""

    _executors: Dict[str, type] = {}

    @classmethod
    def register(cls, node_type: str, executor_class: type):
        """
        실행기 등록

        Args:
            node_type: 노드 타입 이름
            executor_class: 실행기 클래스
        """
        cls._executors[node_type] = executor_class
        logger.info(f"실행기 등록: {node_type} -> {executor_class.__name__}")

    @classmethod
    def get(cls, node_type: str) -> Optional[type]:
        """
        실행기 조회

        Args:
            node_type: 노드 타입 이름

        Returns:
            실행기 클래스 또는 None
        """
        return cls._executors.get(node_type)

    @classmethod
    def get_all_types(cls) -> list[str]:
        """등록된 모든 노드 타입 조회"""
        return list(cls._executors.keys())

    @classmethod
    def create(cls, node_id: str, node_type: str, parameters: Dict[str, Any]):
        """
        실행기 인스턴스 생성

        Args:
            node_id: 노드 ID
            node_type: 노드 타입
            parameters: 노드 파라미터

        Returns:
            실행기 인스턴스

        Raises:
            ValueError: 등록되지 않은 노드 타입이고 Custom API Config도 없는 경우
        """
        executor_class = cls.get(node_type)

        # 등록된 executor가 있으면 사용
        if executor_class is not None:
            return executor_class(node_id, node_type, parameters)

        # 등록된 executor가 없으면 Custom API인지 확인
        logger.info(f"등록되지 않은 노드 타입: {node_type}, Custom API 확인 중...")

        from ..api_config_manager import get_api_config_manager
        from .generic_api_executor import create_generic_executor

        api_config_manager = get_api_config_manager()
        api_config = api_config_manager.get_config(node_type)

        if api_config is not None:
            # Custom API인 경우 GenericAPIExecutor 사용
            logger.info(f"Custom API 발견: {node_type}, GenericAPIExecutor 사용")
            return create_generic_executor(node_id, node_type, parameters, api_config)

        # Custom API도 아니면 에러
        raise ValueError(
            f"알 수 없는 노드 타입: {node_type}. "
            f"등록된 타입: {', '.join(cls.get_all_types())}"
        )
