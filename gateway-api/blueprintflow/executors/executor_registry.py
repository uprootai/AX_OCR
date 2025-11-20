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
            ValueError: 등록되지 않은 노드 타입
        """
        executor_class = cls.get(node_type)
        if executor_class is None:
            raise ValueError(
                f"알 수 없는 노드 타입: {node_type}. "
                f"등록된 타입: {', '.join(cls.get_all_types())}"
            )

        return executor_class(node_id, node_type, parameters)
