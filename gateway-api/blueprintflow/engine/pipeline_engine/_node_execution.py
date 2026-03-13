"""
Node Execution Mixin
단일 노드 실행 및 SSE 이벤트 생성
"""
import asyncio
import time
import logging
import orjson
from typing import Dict, Any, Optional, AsyncGenerator

from ...schemas.workflow import WorkflowDefinition
from ..execution_context import ExecutionContext
from ..input_collector import collect_node_inputs
from ...executors.executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


class NodeExecutionMixin:
    """단일 노드 실행 관련 메서드"""

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

        logger.info(f"노드 실행 시작: {node.id} ({node.type})")
        logger.info(f"노드 파라미터: {node.parameters}")  # 디버깅용
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
                logger.info(f"노드 실행 완료: {node.id}")
            else:
                # 실패
                context.set_node_status(
                    node.id,
                    "failed",
                    progress=0.0,
                    error=result.get("error", "Unknown error"),
                )
                logger.error(f"노드 실행 실패: {node.id} - {result.get('error')}")

        except Exception as e:
            error_msg = str(e)
            context.set_node_status(node.id, "failed", error=error_msg)
            # 빈 출력 설정 (다음 노드가 graceful하게 처리할 수 있도록)
            context.set_node_output(node.id, {"_error": error_msg, "_node_failed": True})
            logger.error(f"노드 실행 중 에러: {node.id} - {e}", exc_info=True)
            # 에러를 raise하지 않음 - 다음 노드가 계속 실행되도록 함

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
                logger.info(f"[SSE] Node {node_id} output keys: {output_keys}, has_image: {has_image}, image_size: {image_size}")
            else:
                logger.warning(f"[SSE] Node {node_id} has NO output!")

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
                        logger.info(f"[결과저장] {node_id}: {list(saved.keys())}")
                except Exception as save_err:
                    logger.warning(f"[결과저장] 노드 결과 저장 실패: {save_err}")

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
