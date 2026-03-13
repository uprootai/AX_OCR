"""
Cancellation Mixin
워크플로우 실행 취소 상태 관리
"""
import asyncio
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CancellationMixin:
    """워크플로우 실행 취소 관련 메서드"""

    _running_executions: Dict[str, asyncio.Event]

    def cancel_execution(self, execution_id: str) -> bool:
        """
        워크플로우 실행 취소

        Args:
            execution_id: 취소할 실행 ID

        Returns:
            취소 성공 여부
        """
        if execution_id in self._running_executions:
            logger.info(f"🛑 워크플로우 실행 취소 요청: {execution_id}")
            self._running_executions[execution_id].set()
            return True
        else:
            logger.warning(f"취소할 실행을 찾을 수 없음: {execution_id}")
            return False

    def get_running_executions(self) -> list:
        """현재 실행 중인 워크플로우 목록"""
        return list(self._running_executions.keys())

    def _is_cancelled(self, execution_id: str) -> bool:
        """실행이 취소되었는지 확인"""
        if execution_id in self._running_executions:
            return self._running_executions[execution_id].is_set()
        return False
