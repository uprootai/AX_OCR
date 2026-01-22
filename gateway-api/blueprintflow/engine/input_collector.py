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
    has_failed_parent = False

    for edge in incoming_edges:
        source_node_id = edge.source
        source_output = context.get_node_output(source_node_id)

        if source_output is None:
            logger.warning(f"부모 노드 {source_node_id}의 출력이 없습니다")
            continue

        # 부모 노드 실패 체크
        if isinstance(source_output, dict) and source_output.get("_node_failed"):
            logger.warning(f"부모 노드 {source_node_id}가 실패했습니다. 에러: {source_output.get('_error')}")
            has_failed_parent = True
            # 실패한 노드의 출력은 건너뛰기 (빈 값 전달)
            continue

        # 출력을 입력으로 병합
        inputs[f"from_{source_node_id}"] = source_output

    # 모든 부모가 실패한 경우 _has_failed_parent 플래그 설정
    if has_failed_parent and not inputs:
        inputs["_has_failed_parent"] = True
        logger.warning(f"노드 {node_id}: 모든 부모 노드가 실패했습니다")

    # 부모가 여러 개인 경우: from_ prefix 유지 (Merge 노드용)
    if len(incoming_edges) > 1:
        logger.debug(f"노드 {node_id}: 부모 {len(incoming_edges)}개, from_ prefix 유지")
        return inputs

    # 부모가 1개인 경우: 단일 딕셔너리로 병합 (일반 노드용)
    merged_inputs = {}
    for parent_output in inputs.values():
        if isinstance(parent_output, dict):
            merged_inputs.update(parent_output)

    return merged_inputs
