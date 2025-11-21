"""
Pipeline Engine
워크플로우 실행 엔진 - DAG 기반 동적 파이프라인 실행
"""
import asyncio
import uuid
import time
import logging
import json
from typing import Dict, Any, Optional, AsyncGenerator

from ..schemas.workflow import (
    WorkflowDefinition,
    WorkflowExecutionResponse,
)
from ..validators.dag_validator import DAGValidator
from ..executors.executor_registry import ExecutorRegistry
from .execution_context import ExecutionContext
from .input_collector import collect_node_inputs

logger = logging.getLogger(__name__)


class PipelineEngine:
    """워크플로우 파이프라인 실행 엔진"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        inputs: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecutionResponse:
        """
        워크플로우 실행

        Args:
            workflow: 워크플로우 정의
            inputs: 초기 입력 데이터
            config: 실행 설정

        Returns:
            실행 결과
        """
        execution_id = str(uuid.uuid4())
        self.logger.info(f"워크플로우 실행 시작: {workflow.name} (ID: {execution_id})")

        try:
            # 1. 검증 단계
            self.logger.info("1단계: DAG 검증")
            nodes_dict = [node.model_dump() for node in workflow.nodes]
            edges_dict = [edge.model_dump() for edge in workflow.edges]

            validator = DAGValidator(nodes_dict, edges_dict)
            is_valid, errors = validator.validate_all()

            if not is_valid:
                error_msg = "; ".join(errors)
                self.logger.error(f"DAG 검증 실패: {error_msg}")
                return WorkflowExecutionResponse(
                    execution_id=execution_id,
                    status="failed",
                    workflow_name=workflow.name,
                    node_statuses=[],
                    error=f"워크플로우 검증 실패: {error_msg}",
                )

            # 2. 실행 준비
            self.logger.info("2단계: 실행 컨텍스트 초기화")
            context = ExecutionContext(execution_id, workflow, inputs)

            # 모든 노드를 pending 상태로 초기화
            for node in workflow.nodes:
                context.set_node_status(node.id, "pending")

            # 3. 위상 정렬
            self.logger.info("3단계: 위상 정렬 및 실행 순서 결정")
            sorted_nodes = validator.topological_sort()
            self.logger.info(f"실행 순서: {' -> '.join(sorted_nodes)}")

            # 4. 병렬 그룹 식별
            parallel_groups = validator.find_parallel_groups()
            self.logger.info(f"병렬 실행 그룹: {parallel_groups}")

            # 5. 노드 실행
            self.logger.info("4단계: 노드 실행")
            for group_idx, node_group in enumerate(parallel_groups):
                self.logger.info(f"그룹 {group_idx + 1}/{len(parallel_groups)} 실행: {node_group}")

                if len(node_group) > 1:
                    # 병렬 실행
                    tasks = [
                        self._execute_node(node_id, workflow, context)
                        for node_id in node_group
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # 에러 체크
                    for node_id, result in zip(node_group, results):
                        if isinstance(result, Exception):
                            self.logger.error(f"노드 {node_id} 실행 중 에러: {result}")
                            context.set_node_status(node_id, "failed", error=str(result))
                else:
                    # 단일 실행
                    node_id = node_group[0]
                    try:
                        await self._execute_node(node_id, workflow, context)
                    except Exception as e:
                        self.logger.error(f"노드 {node_id} 실행 중 에러: {e}")
                        context.set_node_status(node_id, "failed", error=str(e))

            # 6. 결과 집계
            self.logger.info("5단계: 결과 집계")
            execution_time = (time.time() - context.start_time) * 1000

            # 최종 출력 결정 (리프 노드들의 출력)
            leaf_nodes = validator.find_leaf_nodes()
            final_output = {}
            for leaf_id in leaf_nodes:
                leaf_output = context.get_node_output(leaf_id)
                if leaf_output:
                    final_output[leaf_id] = leaf_output

            # 전체 실행 상태 결정
            has_failed = any(s.status == "failed" for s in context.node_statuses.values())
            overall_status = "failed" if has_failed else "completed"

            self.logger.info(f"워크플로우 실행 완료: {overall_status} (소요 시간: {execution_time:.2f}ms)")

            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status=overall_status,
                workflow_name=workflow.name,
                node_statuses=list(context.node_statuses.values()),
                final_output=final_output if final_output else None,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            self.logger.error(f"워크플로우 실행 중 예외 발생: {e}", exc_info=True)
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                status="failed",
                workflow_name=workflow.name,
                node_statuses=[],
                error=f"실행 엔진 에러: {str(e)}",
            )

    async def _execute_node(
        self,
        node_id: str,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
    ):
        """
        단일 노드 실행

        Args:
            node_id: 노드 ID
            workflow: 워크플로우 정의
            context: 실행 컨텍스트
        """
        # 노드 정의 찾기
        node = next((n for n in workflow.nodes if n.id == node_id), None)
        if not node:
            raise ValueError(f"노드를 찾을 수 없습니다: {node_id}")

        self.logger.info(f"노드 실행 시작: {node.id} ({node.type})")
        context.set_node_status(node.id, "running", progress=0.0)

        try:
            # 입력 데이터 수집
            inputs = await collect_node_inputs(node_id, workflow, context)

            # Executor 생성
            executor = ExecutorRegistry.create(
                node_id=node.id,
                node_type=node.type,
                parameters=node.parameters,
            )

            # 실행
            result = await executor.run(inputs, context.global_vars)

            if result["success"]:
                # 성공
                context.set_node_output(node.id, result["data"])
                context.set_node_status(
                    node.id,
                    "completed",
                    progress=1.0,
                    output=result["data"],
                )
                self.logger.info(f"노드 실행 완료: {node.id}")
            else:
                # 실패
                context.set_node_status(
                    node.id,
                    "failed",
                    progress=0.0,
                    error=result.get("error", "Unknown error"),
                )
                self.logger.error(f"노드 실행 실패: {node.id} - {result.get('error')}")

        except Exception as e:
            context.set_node_status(node.id, "failed", error=str(e))
            self.logger.error(f"노드 실행 중 에러: {node.id} - {e}", exc_info=True)
            raise

    async def execute_workflow_stream(
        self,
        workflow: WorkflowDefinition,
        inputs: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        워크플로우 실행 (SSE 스트리밍 버전)

        실행 중 각 노드의 상태 변화를 실시간으로 yield합니다.

        Args:
            workflow: 워크플로우 정의
            inputs: 초기 입력 데이터
            config: 실행 설정

        Yields:
            SSE 포맷 이벤트 문자열
        """
        execution_id = str(uuid.uuid4())
        self.logger.info(f"[SSE] 워크플로우 실행 시작: {workflow.name} (ID: {execution_id})")

        try:
            # 초기 상태 전송
            yield self._format_sse_event({
                "type": "workflow_start",
                "execution_id": execution_id,
                "workflow_name": workflow.name,
                "timestamp": time.time()
            })

            # 1. DAG 검증
            nodes_dict = [node.model_dump() for node in workflow.nodes]
            edges_dict = [edge.model_dump() for edge in workflow.edges]

            validator = DAGValidator(nodes_dict, edges_dict)
            is_valid, errors = validator.validate_all()

            if not is_valid:
                error_msg = "; ".join(errors)
                yield self._format_sse_event({
                    "type": "error",
                    "message": f"워크플로우 검증 실패: {error_msg}"
                })
                return

            # 2. 실행 준비
            context = ExecutionContext(execution_id, workflow, inputs)

            # 모든 노드를 pending 상태로 초기화
            for node in workflow.nodes:
                context.set_node_status(node.id, "pending")

            # 3. 위상 정렬
            sorted_nodes = validator.topological_sort()
            parallel_groups = validator.find_parallel_groups()

            yield self._format_sse_event({
                "type": "execution_plan",
                "sorted_nodes": sorted_nodes,
                "parallel_groups": parallel_groups,
                "total_nodes": len(workflow.nodes)
            })

            # 4. 노드 실행
            for group_idx, node_group in enumerate(parallel_groups):
                if len(node_group) > 1:
                    # 병렬 실행
                    tasks = []
                    for node_id in node_group:
                        tasks.append(self._execute_node_with_events(
                            node_id, workflow, context, self._event_callback
                        ))

                    # 병렬 실행 중 이벤트를 받기 위해 gather 사용
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # 각 노드 완료 이벤트 전송
                    for node_id, result in zip(node_group, results):
                        node_status = context.get_node_status(node_id)
                        if node_status:
                            yield self._format_sse_event({
                                "type": "node_update",
                                "node_id": node_id,
                                "status": node_status.status,
                                "progress": node_status.progress,
                                "error": node_status.error
                            })
                else:
                    # 단일 실행
                    node_id = node_group[0]

                    # 노드 실행 시작 이벤트
                    yield self._format_sse_event({
                        "type": "node_start",
                        "node_id": node_id,
                        "status": "running"
                    })

                    try:
                        await self._execute_node(node_id, workflow, context)
                        node_status = context.get_node_status(node_id)

                        # 노드 완료 이벤트
                        yield self._format_sse_event({
                            "type": "node_complete",
                            "node_id": node_id,
                            "status": node_status.status if node_status else "completed",
                            "progress": node_status.progress if node_status else 1.0
                        })
                    except Exception as e:
                        # 노드 실패 이벤트
                        yield self._format_sse_event({
                            "type": "node_error",
                            "node_id": node_id,
                            "status": "failed",
                            "error": str(e)
                        })

            # 5. 완료
            execution_time = (time.time() - context.start_time) * 1000

            # 최종 출력 결정
            leaf_nodes = validator.find_leaf_nodes()
            final_output = {}
            for leaf_id in leaf_nodes:
                leaf_output = context.get_node_output(leaf_id)
                if leaf_output:
                    final_output[leaf_id] = leaf_output

            # 전체 실행 상태 결정
            has_failed = any(s.status == "failed" for s in context.node_statuses.values())
            overall_status = "failed" if has_failed else "completed"

            # 완료 이벤트 전송
            yield self._format_sse_event({
                "type": "workflow_complete",
                "status": overall_status,
                "execution_time_ms": execution_time,
                "node_statuses": [
                    {
                        "node_id": ns.node_id,
                        "status": ns.status,
                        "progress": ns.progress,
                        "error": ns.error
                    }
                    for ns in context.node_statuses.values()
                ],
                "final_output": final_output if final_output else None
            })

        except Exception as e:
            self.logger.error(f"[SSE] 워크플로우 실행 중 예외: {e}", exc_info=True)
            yield self._format_sse_event({
                "type": "error",
                "message": f"실행 엔진 에러: {str(e)}"
            })

    async def _execute_node_with_events(
        self,
        node_id: str,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        event_callback: Optional[callable] = None
    ):
        """이벤트 콜백을 지원하는 노드 실행"""
        await self._execute_node(node_id, workflow, context)

    def _event_callback(self, event: Dict[str, Any]):
        """노드 실행 중 이벤트 콜백 (추후 확장 가능)"""
        pass

    def _format_sse_event(self, data: Dict[str, Any]) -> str:
        """SSE 이벤트 포맷 생성"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
