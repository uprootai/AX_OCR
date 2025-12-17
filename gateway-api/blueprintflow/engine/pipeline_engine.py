"""
Pipeline Engine
워크플로우 실행 엔진 - DAG 기반 동적 파이프라인 실행
"""
import asyncio
import uuid
import time
import logging
import json
import os
import orjson  # 고성능 JSON 직렬화
from typing import Dict, Any, Optional, AsyncGenerator

from ..schemas.workflow import (
    WorkflowDefinition,
    WorkflowExecutionResponse,
)
from ..validators.dag_validator import DAGValidator
from ..executors.executor_registry import ExecutorRegistry
from .execution_context import ExecutionContext
from .input_collector import collect_node_inputs

# 결과 저장 기능
try:
    from utils.result_manager import get_result_manager
    RESULT_SAVING_ENABLED = os.getenv("ENABLE_RESULT_SAVING", "true").lower() == "true"
except ImportError:
    RESULT_SAVING_ENABLED = False
    get_result_manager = None

logger = logging.getLogger(__name__)


class PipelineEngine:
    """워크플로우 파이프라인 실행 엔진"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.result_manager = get_result_manager() if RESULT_SAVING_ENABLED and get_result_manager else None
        self.node_execution_order = 0  # 노드 실행 순서 추적
        # 실행 중인 워크플로우 추적 (취소용)
        self._running_executions: Dict[str, asyncio.Event] = {}

    def cancel_execution(self, execution_id: str) -> bool:
        """
        워크플로우 실행 취소

        Args:
            execution_id: 취소할 실행 ID

        Returns:
            취소 성공 여부
        """
        if execution_id in self._running_executions:
            self.logger.info(f"🛑 워크플로우 실행 취소 요청: {execution_id}")
            self._running_executions[execution_id].set()
            return True
        else:
            self.logger.warning(f"취소할 실행을 찾을 수 없음: {execution_id}")
            return False

    def get_running_executions(self) -> list:
        """현재 실행 중인 워크플로우 목록"""
        return list(self._running_executions.keys())

    def _is_cancelled(self, execution_id: str) -> bool:
        """실행이 취소되었는지 확인"""
        if execution_id in self._running_executions:
            return self._running_executions[execution_id].is_set()
        return False

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
            config: 실행 설정 (execution_mode: 'sequential' | 'parallel')

        Returns:
            실행 결과
        """
        execution_id = str(uuid.uuid4())

        # 실행 모드 결정 (기본값: sequential)
        execution_mode = (config or {}).get("execution_mode", "sequential")
        self.logger.info(f"워크플로우 실행 시작: {workflow.name} (ID: {execution_id}, 모드: {execution_mode})")

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

            if execution_mode == "sequential":
                # 순차 실행: 위상 정렬 순서대로 하나씩 실행
                self.logger.info("🔄 순차 실행 모드")
                for node_id in sorted_nodes:
                    try:
                        self.logger.info(f"노드 실행: {node_id}")
                        await self._execute_node(node_id, workflow, context)
                    except Exception as e:
                        self.logger.error(f"노드 {node_id} 실행 중 에러: {e}")
                        context.set_node_status(node_id, "failed", error=str(e))
            else:
                # 병렬 실행: 병렬 그룹 단위로 실행
                self.logger.info("⚡ 병렬 실행 모드")
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
        self.logger.info(f"노드 파라미터: {node.parameters}")  # 디버깅용
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
            config: 실행 설정 (execution_mode: 'sequential' | 'parallel')

        Yields:
            SSE 포맷 이벤트 문자열
        """
        execution_id = str(uuid.uuid4())

        # 실행 모드 결정 (기본값: sequential)
        execution_mode = (config or {}).get("execution_mode", "sequential")
        self.logger.info(f"[SSE] 워크플로우 실행 시작: {workflow.name} (ID: {execution_id}, 모드: {execution_mode})")

        # 취소 플래그 등록
        cancel_event = asyncio.Event()
        self._running_executions[execution_id] = cancel_event

        # 결과 저장 세션 초기화
        self.node_execution_order = 0
        session_dir = None
        if self.result_manager:
            try:
                session_dir = self.result_manager.create_session(workflow.name)
                self.logger.info(f"[결과저장] 세션 생성: {session_dir}")
            except Exception as e:
                self.logger.warning(f"[결과저장] 세션 생성 실패: {e}")

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
                "execution_mode": execution_mode,
                "total_nodes": len(workflow.nodes)
            })

            # 4. 노드 실행
            if execution_mode == "sequential":
                # 순차 실행: 위상 정렬 순서대로 하나씩 실행
                self.logger.info("🔄 [SSE] 순차 실행 모드")
                for node_id in sorted_nodes:
                    # 취소 확인
                    if self._is_cancelled(execution_id):
                        self.logger.info(f"🛑 [SSE] 워크플로우 취소됨 (노드 {node_id} 실행 전)")
                        yield self._format_sse_event({
                            "type": "workflow_cancelled",
                            "execution_id": execution_id,
                            "cancelled_at_node": node_id,
                            "message": "Workflow cancelled by user"
                        })
                        return

                    # 노드 실행 시작 이벤트
                    yield self._format_sse_event({
                        "type": "node_start",
                        "node_id": node_id,
                        "status": "running"
                    })

                    async for event in self._execute_single_node_stream(
                        node_id, workflow, context, session_dir
                    ):
                        yield event
            else:
                # 병렬 실행: 병렬 그룹 단위로 실행
                self.logger.info("⚡ [SSE] 병렬 실행 모드")
                for group_idx, node_group in enumerate(parallel_groups):
                    # 취소 확인
                    if self._is_cancelled(execution_id):
                        self.logger.info(f"🛑 [SSE] 워크플로우 취소됨 (그룹 {group_idx + 1} 실행 전)")
                        yield self._format_sse_event({
                            "type": "workflow_cancelled",
                            "execution_id": execution_id,
                            "cancelled_at_group": group_idx + 1,
                            "message": "Workflow cancelled by user"
                        })
                        return

                    if len(node_group) > 1:
                        # 병렬 실행
                        tasks = []
                        for node_id in node_group:
                            tasks.append(self._execute_node_with_events(
                                node_id, workflow, context, self._event_callback
                            ))

                        # 병렬 실행 중 이벤트를 받기 위해 gather 사용
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        # 각 노드 완료 이벤트 전송 및 결과 저장
                        for node_id, result in zip(node_group, results):
                            node_status = context.get_node_status(node_id)
                            if node_status:
                                # 결과 저장
                                if self.result_manager and session_dir and node_status.output:
                                    try:
                                        node = next((n for n in workflow.nodes if n.id == node_id), None)
                                        self.node_execution_order += 1
                                        self.result_manager.save_node_result(
                                            node_id=node_id,
                                            node_type=node.type if node else "unknown",
                                            result=node_status.output,
                                            execution_order=self.node_execution_order,
                                            session_dir=session_dir
                                        )
                                    except Exception as save_err:
                                        self.logger.warning(f"[결과저장] 병렬 노드 저장 실패: {save_err}")

                                yield self._format_sse_event({
                                    "type": "node_update",
                                    "node_id": node_id,
                                    "status": node_status.status,
                                    "progress": node_status.progress,
                                    "error": node_status.error,
                                    "output": node_status.output
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

                        async for event in self._execute_single_node_stream(
                            node_id, workflow, context, session_dir
                        ):
                            yield event

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

            # 워크플로우 메타데이터 저장
            if self.result_manager and session_dir:
                try:
                    self.result_manager.save_workflow_metadata(
                        workflow_name=workflow.name,
                        nodes=[n.model_dump() for n in workflow.nodes],
                        execution_time=execution_time / 1000,  # ms -> seconds
                        status=overall_status,
                        session_dir=session_dir
                    )
                    self.logger.info(f"[결과저장] 워크플로우 메타데이터 저장 완료: {session_dir}")
                except Exception as meta_err:
                    self.logger.warning(f"[결과저장] 메타데이터 저장 실패: {meta_err}")

            # 완료 이벤트 전송
            yield self._format_sse_event({
                "type": "workflow_complete",
                "status": overall_status,
                "execution_time_ms": execution_time,
                "result_save_path": str(session_dir) if session_dir else None,  # 저장 경로 추가
                "node_statuses": [
                    {
                        "node_id": ns.node_id,
                        "status": ns.status,
                        "progress": ns.progress,
                        "error": ns.error,
                        "output": ns.output  # ✅ output 추가 (이미지 포함)
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
        finally:
            # 실행 정보 정리
            if execution_id in self._running_executions:
                del self._running_executions[execution_id]
                self.logger.info(f"[SSE] 워크플로우 실행 정보 정리: {execution_id}")

    async def _execute_node_with_events(
        self,
        node_id: str,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        event_callback: Optional[callable] = None
    ):
        """이벤트 콜백을 지원하는 노드 실행"""
        await self._execute_node(node_id, workflow, context)

    async def _execute_single_node_stream(
        self,
        node_id: str,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        session_dir: Optional[Any] = None
    ) -> AsyncGenerator[str, None]:
        """단일 노드 실행 및 SSE 이벤트 생성 (순차/병렬 모드 공용)"""
        try:
            # 하트비트와 함께 노드 실행
            start_time = time.time()
            heartbeat_interval = 5  # 5초마다 하트비트

            # 노드 실행을 Task로 시작
            execute_task = asyncio.create_task(
                self._execute_node(node_id, workflow, context)
            )

            # 실행 완료까지 하트비트 전송
            while not execute_task.done():
                try:
                    # 5초 대기 또는 실행 완료
                    await asyncio.wait_for(
                        asyncio.shield(execute_task),
                        timeout=heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    # 타임아웃 = 아직 실행 중 → 하트비트 전송
                    elapsed = int(time.time() - start_time)
                    yield self._format_sse_event({
                        "type": "node_heartbeat",
                        "node_id": node_id,
                        "status": "running",
                        "elapsed_seconds": elapsed,
                        "message": f"처리 중... ({elapsed}초 경과)"
                    })

            # Task 완료 후 예외 확인
            await execute_task

            node_status = context.get_node_status(node_id)

            # 디버그: output 확인
            output_data = node_status.output if node_status else None
            if output_data:
                output_keys = list(output_data.keys()) if isinstance(output_data, dict) else []
                has_image = 'image' in output_keys or 'visualized_image' in output_keys
                image_size = len(output_data.get('image', '') or output_data.get('visualized_image', '') or '') if has_image else 0
                self.logger.info(f"[SSE] Node {node_id} output keys: {output_keys}, has_image: {has_image}, image_size: {image_size}")
            else:
                self.logger.warning(f"[SSE] Node {node_id} has NO output!")

            # 결과 저장
            if self.result_manager and session_dir and output_data:
                try:
                    node = next((n for n in workflow.nodes if n.id == node_id), None)
                    self.node_execution_order += 1
                    saved = self.result_manager.save_node_result(
                        node_id=node_id,
                        node_type=node.type if node else "unknown",
                        result=output_data,
                        execution_order=self.node_execution_order,
                        session_dir=session_dir
                    )
                    if saved:
                        self.logger.info(f"[결과저장] {node_id}: {list(saved.keys())}")
                except Exception as save_err:
                    self.logger.warning(f"[결과저장] 노드 결과 저장 실패: {save_err}")

            # 노드 완료 이벤트
            yield self._format_sse_event({
                "type": "node_complete",
                "node_id": node_id,
                "status": node_status.status if node_status else "completed",
                "progress": node_status.progress if node_status else 1.0,
                "output": output_data
            })
        except Exception as e:
            # 노드 실패 이벤트
            yield self._format_sse_event({
                "type": "node_error",
                "node_id": node_id,
                "status": "failed",
                "error": str(e)
            })

    def _event_callback(self, event: Dict[str, Any]):
        """노드 실행 중 이벤트 콜백 (추후 확장 가능)"""
        pass

    def _format_sse_event(self, data: Dict[str, Any]) -> str:
        """SSE 이벤트 포맷 생성 (orjson으로 최적화)"""
        # orjson은 bytes 반환, decode 필요
        json_str = orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS).decode('utf-8')
        return f"data: {json_str}\n\n"
