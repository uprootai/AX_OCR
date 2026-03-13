"""
Eager Execution Mixin
DAG 의존성 기반 즉시 실행 (비스트리밍 + SSE 스트리밍)
"""
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator

from ...schemas.workflow import WorkflowDefinition
from ..execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class EagerExecutionMixin:
    """Eager 실행 관련 메서드 (의존성 충족 시 즉시 실행)"""

    async def _execute_eager(
        self,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        sorted_nodes: list,
    ):
        """Eager 실행 (비스트리밍): 각 노드의 직접 의존성 완료 시 즉시 실행"""
        # 의존성 맵 구축
        deps: Dict[str, set] = {}
        for node in workflow.nodes:
            parent_ids = set()
            for edge in workflow.edges:
                if edge.target == node.id:
                    parent_ids.add(edge.source)
            deps[node.id] = parent_ids

        completed: set = set()
        running: Dict[str, asyncio.Task] = {}
        pending = set(n.id for n in workflow.nodes)

        while pending or running:
            # 의존성 충족된 노드 찾아 시작
            ready = [nid for nid in pending if deps[nid].issubset(completed)]
            for nid in ready:
                pending.discard(nid)
                task = asyncio.create_task(self._execute_node(nid, workflow, context))
                running[nid] = task

            if not running:
                break

            # 하나라도 완료될 때까지 대기
            done, _ = await asyncio.wait(
                running.values(), return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                nid = next(k for k, v in running.items() if v is task)
                del running[nid]
                completed.add(nid)

    async def _execute_eager_stream(
        self,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        sorted_nodes: list,
        session_dir: Optional[Any],
        execution_id: str,
    ) -> AsyncGenerator[str, None]:
        """Eager 실행 (SSE 스트리밍): 각 노드의 직접 의존성 완료 시 즉시 실행"""
        # 의존성 맵 구축
        deps: Dict[str, set] = {}
        for node in workflow.nodes:
            parent_ids = set()
            for edge in workflow.edges:
                if edge.target == node.id:
                    parent_ids.add(edge.source)
            deps[node.id] = parent_ids

        completed: set = set()
        running: Dict[str, asyncio.Task] = {}
        pending = set(n.id for n in workflow.nodes)

        while pending or running:
            # 취소 확인
            if self._is_cancelled(execution_id):
                # 실행 중인 태스크 취소
                for task in running.values():
                    task.cancel()
                yield self._format_sse_event({
                    "type": "workflow_cancelled",
                    "execution_id": execution_id,
                    "message": "Workflow cancelled by user",
                })
                return

            # 의존성 충족된 노드 찾아 즉시 시작
            ready = [nid for nid in pending if deps[nid].issubset(completed)]
            for nid in ready:
                pending.discard(nid)
                yield self._format_sse_event({
                    "type": "node_start",
                    "node_id": nid,
                    "status": "running",
                })
                task = asyncio.create_task(self._execute_node(nid, workflow, context))
                running[nid] = task

            if not running:
                break

            # 하나라도 완료될 때까지 대기 (+ 하트비트)
            done, _ = await asyncio.wait(
                running.values(),
                return_when=asyncio.FIRST_COMPLETED,
                timeout=5,
            )

            if not done:
                # 타임아웃 = 하트비트 전송
                for nid in running:
                    yield self._format_sse_event({
                        "type": "node_heartbeat",
                        "node_id": nid,
                        "status": "running",
                        "message": "처리 중...",
                    })
                continue

            # 완료된 노드 처리
            for task in done:
                nid = next(k for k, v in running.items() if v is task)
                del running[nid]
                completed.add(nid)

                node_status = context.get_node_status(nid)
                output_data = node_status.output if node_status else None

                # 결과 저장
                if self.result_manager and session_dir and output_data:
                    try:
                        node = next((n for n in workflow.nodes if n.id == nid), None)
                        self.node_execution_order += 1
                        self.result_manager.save_node_result(
                            node_id=nid,
                            node_type=node.type if node else "unknown",
                            result=output_data,
                            execution_order=self.node_execution_order,
                            session_dir=session_dir,
                        )
                    except Exception as save_err:
                        logger.warning(f"[결과저장] eager 노드 저장 실패: {save_err}")

                yield self._format_sse_event({
                    "type": "node_complete",
                    "node_id": nid,
                    "status": node_status.status if node_status else "completed",
                    "progress": node_status.progress if node_status else 1.0,
                    "output": output_data,
                })
