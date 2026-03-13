"""
Pipeline Engine
워크플로우 실행 엔진 - 믹스인 조합
"""
import asyncio
import logging
import os
from typing import Dict

from ._cancellation import CancellationMixin
from ._node_execution import NodeExecutionMixin
from ._eager_execution import EagerExecutionMixin
from ._workflow_execution import WorkflowExecutionMixin

# 결과 저장 기능
try:
    from utils.result_manager import get_result_manager
    RESULT_SAVING_ENABLED = os.getenv("ENABLE_RESULT_SAVING", "true").lower() == "true"
except ImportError:
    RESULT_SAVING_ENABLED = False
    get_result_manager = None

logger = logging.getLogger(__name__)


class PipelineEngine(
    CancellationMixin,
    NodeExecutionMixin,
    EagerExecutionMixin,
    WorkflowExecutionMixin,
):
    """워크플로우 파이프라인 실행 엔진"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.result_manager = get_result_manager() if RESULT_SAVING_ENABLED and get_result_manager else None
        self.node_execution_order = 0  # 노드 실행 순서 추적
        # 실행 중인 워크플로우 추적 (취소용)
        self._running_executions: Dict[str, asyncio.Event] = {}
