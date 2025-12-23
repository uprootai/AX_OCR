"""
Workflow Router
BlueprintFlow 워크플로우 실행 엔드포인트
"""

import json
import base64
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from blueprintflow import (
    PipelineEngine,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowDefinition,
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


async def _parse_workflow_request(request: Request) -> WorkflowExecutionRequest:
    """
    요청 Content-Type에 따라 JSON 또는 Multipart 형식을 파싱합니다.

    - JSON: { workflow: {...}, inputs: {...}, config: {...} }
    - Multipart: workflow (JSON string) + file (binary image)
    """
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        # Multipart form data 파싱
        logger.info("[SSE] Multipart 형식 요청 감지")
        form = await request.form()

        # workflow JSON 파싱
        workflow_json = form.get("workflow")
        if not workflow_json:
            raise HTTPException(status_code=400, detail="Missing 'workflow' field in multipart request")

        try:
            workflow_data = json.loads(workflow_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in 'workflow' field: {e}")

        # inputs와 config 준비
        inputs = workflow_data.pop("inputs", {}) if "inputs" in workflow_data else {}
        config = workflow_data.pop("config", {}) if "config" in workflow_data else {}

        # file이 있으면 base64로 변환하여 inputs에 추가
        file = form.get("file")
        if file and hasattr(file, "read"):
            file_content = await file.read()
            file_base64 = base64.b64encode(file_content).decode("utf-8")
            # MIME type 추출
            content_type_header = getattr(file, "content_type", "image/jpeg")
            inputs["image"] = f"data:{content_type_header};base64,{file_base64}"
            logger.info(f"[SSE] 파일 변환: {getattr(file, 'filename', 'unknown')} -> base64 ({len(file_content)} bytes)")

        # WorkflowDefinition이 workflow_data에 직접 있는 경우 처리
        if "nodes" in workflow_data and "edges" in workflow_data:
            workflow_def = WorkflowDefinition(**workflow_data)
        elif "workflow" in workflow_data:
            workflow_def = WorkflowDefinition(**workflow_data["workflow"])
        else:
            raise HTTPException(status_code=400, detail="Invalid workflow structure: missing 'nodes' and 'edges'")

        return WorkflowExecutionRequest(
            workflow=workflow_def,
            inputs=inputs,
            config=config
        )

    else:
        # JSON body 파싱 (기본)
        logger.info("[SSE] JSON 형식 요청 감지")
        try:
            body = await request.body()
            data = json.loads(body)
            return WorkflowExecutionRequest(**data)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid request format: {e}")


@router.post("/execute-stream")
async def execute_workflow_stream(request: Request):
    """
    BlueprintFlow 워크플로우 실행 엔드포인트 (SSE 스트리밍)

    실시간으로 워크플로우 실행 진행상황을 Server-Sent Events로 전송합니다.

    지원 형식:
    - JSON: Content-Type: application/json
      Body: { "workflow": {...}, "inputs": {...}, "config": {...} }
    - Multipart: Content-Type: multipart/form-data
      Fields: workflow (JSON string), file (optional binary image)
    """
    try:
        # Content-Type에 따라 요청 파싱
        exec_request = await _parse_workflow_request(request)
        logger.info(f"[SSE] 워크플로우 실행 요청: {exec_request.workflow.name}")

        async def event_stream():
            try:
                async for event in blueprint_engine.execute_workflow_stream(
                    workflow=exec_request.workflow,
                    inputs=exec_request.inputs,
                    config=exec_request.config,
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

    except HTTPException:
        raise
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
