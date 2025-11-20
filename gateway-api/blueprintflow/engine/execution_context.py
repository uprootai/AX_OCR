"""
Execution Context
워크플로우 실행 중 상태 관리
"""
import time
from typing import Dict, Any, Optional

from ..schemas.workflow import WorkflowDefinition, NodeExecutionStatus


class ExecutionContext:
    """실행 컨텍스트 - 워크플로우 실행 중 상태 관리"""

    def __init__(self, execution_id: str, workflow: WorkflowDefinition, initial_inputs: Dict[str, Any]):
        self.execution_id = execution_id
        self.workflow = workflow
        self.initial_inputs = initial_inputs

        # 노드별 실행 결과 저장
        self.node_outputs: Dict[str, Any] = {}

        # 노드별 실행 상태
        self.node_statuses: Dict[str, NodeExecutionStatus] = {}

        # 전역 변수 (모든 노드가 접근 가능)
        self.global_vars: Dict[str, Any] = {"inputs": initial_inputs}

        # 실행 시작 시간
        self.start_time = time.time()

    def set_node_status(
        self,
        node_id: str,
        status: str,
        progress: float = 0.0,
        error: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None,
    ):
        """노드 실행 상태 업데이트"""
        if node_id not in self.node_statuses:
            self.node_statuses[node_id] = NodeExecutionStatus(
                node_id=node_id,
                status=status,
                progress=progress,
            )
        else:
            self.node_statuses[node_id].status = status
            self.node_statuses[node_id].progress = progress

        if error:
            self.node_statuses[node_id].error = error
        if output:
            self.node_statuses[node_id].output = output

        # 시간 기록
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if status == "running" and not self.node_statuses[node_id].start_time:
            self.node_statuses[node_id].start_time = current_time
        elif status in ["completed", "failed", "skipped"]:
            self.node_statuses[node_id].end_time = current_time

    def get_node_output(self, node_id: str) -> Optional[Dict[str, Any]]:
        """특정 노드의 실행 결과 조회"""
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: Dict[str, Any]):
        """노드 실행 결과 저장"""
        self.node_outputs[node_id] = output

    def get_execution_summary(self) -> Dict[str, Any]:
        """실행 요약 정보"""
        total_nodes = len(self.workflow.nodes)
        completed = sum(1 for s in self.node_statuses.values() if s.status == "completed")
        failed = sum(1 for s in self.node_statuses.values() if s.status == "failed")

        return {
            "execution_id": self.execution_id,
            "workflow_name": self.workflow.name,
            "total_nodes": total_nodes,
            "completed_nodes": completed,
            "failed_nodes": failed,
            "progress": completed / total_nodes if total_nodes > 0 else 0,
            "elapsed_time_ms": (time.time() - self.start_time) * 1000,
        }
