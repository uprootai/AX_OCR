"""
Input Collector
노드 입력 데이터 수집 로직
"""
import logging
from typing import Dict, Any

from ..schemas.workflow import WorkflowDefinition
from .execution_context import ExecutionContext

logger = logging.getLogger(__name__)


async def collect_node_inputs(
    node_id: str,
    workflow: WorkflowDefinition,
    context: ExecutionContext,
) -> Dict[str, Any]:
    """
    노드의 입력 데이터 수집

    Args:
        node_id: 노드 ID
        workflow: 워크플로우 정의
        context: 실행 컨텍스트

    Returns:
        수집된 입력 데이터
    """
    # 이 노드로 들어오는 엣지 찾기
    incoming_edges = [e for e in workflow.edges if e.target == node_id]

    if not incoming_edges:
        # 루트 노드 - 초기 입력 사용
        return context.initial_inputs

    # 부모 노드들의 출력 수집
    inputs = {}
    for edge in incoming_edges:
        source_node_id = edge.source
        source_output = context.get_node_output(source_node_id)

        if source_output is None:
            logger.warning(f"부모 노드 {source_node_id}의 출력이 없습니다")
            continue

        # 출력을 입력으로 병합
        inputs[f"from_{source_node_id}"] = source_output

    # 모든 부모 출력을 단일 딕셔너리로 병합 (키 충돌 시 마지막 값 사용)
    merged_inputs = {}
    for parent_output in inputs.values():
        if isinstance(parent_output, dict):
            merged_inputs.update(parent_output)

    return merged_inputs
