"""
Workflow Router
BlueprintFlow 워크플로우 실행 엔드포인트
"""

import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from blueprintflow import (
    PipelineEngine,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
)
from blueprintflow.executors.executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])

# PipelineEngine 인스턴스 (싱글톤)
blueprint_engine = PipelineEngine()


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(request: WorkflowExecutionRequest):
    """
    BlueprintFlow 워크플로우 실행 엔드포인트

    사용자가 정의한 워크플로우를 동적으로 실행합니다.
    """
    try:
        logger.info(f"워크플로우 실행 요청: {request.workflow.name}")

        result = await blueprint_engine.execute_workflow(
            workflow=request.workflow,
            inputs=request.inputs,
            config=request.config,
        )

        return result

    except Exception as e:
        logger.error(f"워크플로우 실행 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-stream")
async def execute_workflow_stream(request: WorkflowExecutionRequest):
    """
    BlueprintFlow 워크플로우 실행 엔드포인트 (SSE 스트리밍)

    실시간으로 워크플로우 실행 진행상황을 Server-Sent Events로 전송합니다.
    """
    try:
        logger.info(f"[SSE] 워크플로우 실행 요청: {request.workflow.name}")

        async def event_stream():
            try:
                async for event in blueprint_engine.execute_workflow_stream(
                    workflow=request.workflow,
                    inputs=request.inputs,
                    config=request.config,
                ):
                    yield event

            except Exception as e:
                logger.error(f"[SSE] 스트림 중 에러: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
            }
        )

    except Exception as e:
        logger.error(f"[SSE] 워크플로우 실행 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node-types")
async def get_available_node_types():
    """사용 가능한 노드 타입 목록 조회"""
    node_types = ExecutorRegistry.get_all_types()

    return {
        "node_types": node_types,
        "count": len(node_types),
        "categories": {
            "api_nodes": [nt for nt in node_types if nt in ["yolo", "edocr2", "edgnet", "skinmodel", "vl", "paddleocr"]],
            "control_nodes": [nt for nt in node_types if nt in ["if", "merge", "loop"]],
        }
    }


@router.get("/health")
async def workflow_health():
    """BlueprintFlow 시스템 상태 체크"""
    return {
        "status": "healthy",
        "engine": "PipelineEngine",
        "version": "1.0.0",
        "features": {
            "dag_validation": True,
            "parallel_execution": True,
            "conditional_branching": False,
            "loop_execution": False,
        }
    }


@router.post("/cancel/{execution_id}")
async def cancel_workflow(execution_id: str):
    """
    워크플로우 실행 취소

    실행 중인 워크플로우를 취소합니다.
    다음 노드 실행 시작 전에 취소가 적용됩니다.
    """
    logger.info(f"워크플로우 취소 요청: {execution_id}")
    success = blueprint_engine.cancel_execution(execution_id)

    if success:
        return {
            "status": "cancelled",
            "execution_id": execution_id,
            "message": "Workflow cancellation requested"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found or already completed: {execution_id}"
        )


@router.get("/running")
async def get_running_workflows():
    """
    실행 중인 워크플로우 목록 조회
    """
    running = blueprint_engine.get_running_executions()
    return {
        "status": "success",
        "running_executions": running,
        "count": len(running)
    }
