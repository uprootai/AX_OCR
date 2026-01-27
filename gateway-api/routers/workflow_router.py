"""
Workflow Router
BlueprintFlow 워크플로우 실행 엔드포인트
"""

import json
import base64
import logging
import os
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
import httpx

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

# Blueprint AI BOM API URL (템플릿 관리)
BOM_API_URL = os.getenv("BOM_API_URL", "http://localhost:5020")


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


# =============================================================================
# Template-based Workflow Execution (P2-2)
# =============================================================================

@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None, description="템플릿 카테고리 필터"),
    drawing_type: Optional[str] = Query(None, description="도면 타입 필터"),
):
    """
    사용 가능한 워크플로우 템플릿 목록 조회

    Blueprint AI BOM의 템플릿 서비스에서 템플릿 목록을 가져옵니다.

    Args:
        category: 템플릿 카테고리 필터 (예: "detection", "analysis")
        drawing_type: 도면 타입 필터 (예: "PID", "MECHANICAL")

    Returns:
        템플릿 목록
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {}
            if category:
                params["category"] = category
            if drawing_type:
                params["drawing_type"] = drawing_type

            response = await client.get(
                f"{BOM_API_URL}/templates",
                params=params,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "templates": data.get("templates", []),
                    "total": data.get("total", 0),
                    "source": "blueprint-ai-bom",
                }
            else:
                logger.warning(f"BOM API 응답 오류: {response.status_code}")
                return {
                    "status": "warning",
                    "templates": [],
                    "total": 0,
                    "message": f"BOM API 응답 오류: {response.status_code}",
                }

    except httpx.ConnectError:
        logger.warning("BOM API 연결 실패 - 기본 템플릿 반환")
        return {
            "status": "fallback",
            "templates": _get_builtin_templates(),
            "total": len(_get_builtin_templates()),
            "message": "BOM API 연결 실패 - 내장 템플릿 사용",
        }
    except Exception as e:
        logger.error(f"템플릿 목록 조회 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    특정 워크플로우 템플릿 상세 조회

    Args:
        template_id: 템플릿 ID

    Returns:
        템플릿 상세 정보 (nodes, edges 포함)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BOM_API_URL}/templates/{template_id}")

            if response.status_code == 200:
                template = response.json()
                return {
                    "status": "success",
                    "template": template,
                }
            elif response.status_code == 404:
                # 내장 템플릿에서 검색
                builtin = _get_builtin_template(template_id)
                if builtin:
                    return {
                        "status": "success",
                        "template": builtin,
                        "source": "builtin",
                    }
                raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"BOM API 오류: {response.text}"
                )

    except HTTPException:
        raise
    except httpx.ConnectError:
        # 내장 템플릿에서 검색
        builtin = _get_builtin_template(template_id)
        if builtin:
            return {
                "status": "success",
                "template": builtin,
                "source": "builtin",
            }
        raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")
    except Exception as e:
        logger.error(f"템플릿 조회 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-template/{template_id}")
async def execute_template(
    template_id: str,
    inputs: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
):
    """
    템플릿 기반 워크플로우 실행

    템플릿 ID로 워크플로우를 조회하고 실행합니다.

    Args:
        template_id: 템플릿 ID
        inputs: 워크플로우 입력 데이터 (예: {"image": "data:image/png;base64,..."})
        config: 실행 설정

    Returns:
        WorkflowExecutionResponse
    """
    try:
        # 1. 템플릿 조회
        template_response = await get_template(template_id)
        template = template_response.get("template", {})

        if not template:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        # 2. 템플릿에서 워크플로우 정의 추출
        nodes = template.get("nodes", [])
        edges = template.get("edges", [])

        if not nodes:
            raise HTTPException(status_code=400, detail="템플릿에 노드가 없습니다")

        # 3. WorkflowDefinition 생성
        workflow_def = WorkflowDefinition(
            name=template.get("name", f"template-{template_id}"),
            description=template.get("description", ""),
            nodes=nodes,
            edges=edges,
        )

        logger.info(f"템플릿 기반 실행: {template_id} -> {workflow_def.name} (노드: {len(nodes)}개)")

        # 4. 워크플로우 실행
        result = await blueprint_engine.execute_workflow(
            workflow=workflow_def,
            inputs=inputs or {},
            config=config or {},
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 실행 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-template-stream/{template_id}")
async def execute_template_stream(
    request: Request,
    template_id: str,
):
    """
    템플릿 기반 워크플로우 실행 (SSE 스트리밍)

    템플릿 ID로 워크플로우를 조회하고 SSE로 실행 진행상황을 전송합니다.

    지원 형식:
    - JSON: Content-Type: application/json
      Body: { "inputs": {...}, "config": {...} }
    - Multipart: Content-Type: multipart/form-data
      Fields: file (optional binary image), inputs (optional JSON string)
    """
    try:
        # 1. 템플릿 조회
        template_response = await get_template(template_id)
        template = template_response.get("template", {})

        if not template:
            raise HTTPException(status_code=404, detail=f"템플릿을 찾을 수 없습니다: {template_id}")

        # 2. 요청 파싱
        content_type = request.headers.get("content-type", "")
        inputs = {}
        config = {}

        if "multipart/form-data" in content_type:
            form = await request.form()

            # 파일 처리
            file = form.get("file")
            if file and hasattr(file, "read"):
                file_content = await file.read()
                file_base64 = base64.b64encode(file_content).decode("utf-8")
                content_type_header = getattr(file, "content_type", "image/jpeg")
                inputs["image"] = f"data:{content_type_header};base64,{file_base64}"
                logger.info(f"[SSE-Template] 파일 변환: {getattr(file, 'filename', 'unknown')}")

            # inputs JSON 처리
            inputs_json = form.get("inputs")
            if inputs_json:
                try:
                    inputs.update(json.loads(inputs_json))
                except json.JSONDecodeError:
                    pass

            # config JSON 처리
            config_json = form.get("config")
            if config_json:
                try:
                    config = json.loads(config_json)
                except json.JSONDecodeError:
                    pass
        else:
            # JSON body 파싱
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    inputs = data.get("inputs", {})
                    config = data.get("config", {})
            except json.JSONDecodeError:
                pass

        # 3. WorkflowDefinition 생성
        nodes = template.get("nodes", [])
        edges = template.get("edges", [])

        workflow_def = WorkflowDefinition(
            name=template.get("name", f"template-{template_id}"),
            description=template.get("description", ""),
            nodes=nodes,
            edges=edges,
        )

        logger.info(f"[SSE-Template] 템플릿 실행: {template_id} -> {workflow_def.name}")

        # 4. SSE 스트리밍 실행
        async def event_stream():
            try:
                async for event in blueprint_engine.execute_workflow_stream(
                    workflow=workflow_def,
                    inputs=inputs,
                    config=config,
                ):
                    yield event

            except Exception as e:
                logger.error(f"[SSE-Template] 스트림 중 에러: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SSE-Template] 워크플로우 실행 중 에러: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Built-in Templates (BOM API 연결 실패 시 폴백)
# =============================================================================

def _get_builtin_templates() -> List[Dict[str, Any]]:
    """내장 기본 템플릿 목록"""
    return [
        {
            "id": "yolo-detection",
            "name": "YOLO 객체 검출",
            "description": "YOLO를 사용한 도면 객체 검출",
            "category": "detection",
            "drawing_type": "general",
            "created_at": "2026-01-01T00:00:00",
        },
        {
            "id": "ocr-extraction",
            "name": "OCR 텍스트 추출",
            "description": "eDOCr2를 사용한 치수 및 텍스트 추출",
            "category": "ocr",
            "drawing_type": "general",
            "created_at": "2026-01-01T00:00:00",
        },
        {
            "id": "full-analysis",
            "name": "전체 분석 파이프라인",
            "description": "YOLO 검출 + OCR 추출 + 공차 분석",
            "category": "analysis",
            "drawing_type": "mechanical",
            "created_at": "2026-01-01T00:00:00",
        },
    ]


def _get_builtin_template(template_id: str) -> Optional[Dict[str, Any]]:
    """내장 템플릿 상세 조회"""
    templates = {
        "yolo-detection": {
            "id": "yolo-detection",
            "name": "YOLO 객체 검출",
            "description": "YOLO를 사용한 도면 객체 검출",
            "category": "detection",
            "drawing_type": "general",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "imageInput",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "이미지 입력"},
                },
                {
                    "id": "yolo-1",
                    "type": "yolo",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "YOLO 검출",
                        "params": {
                            "model_type": "engineering",
                            "confidence": 0.5,
                            "visualize": True,
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "yolo-1"},
            ],
        },
        "ocr-extraction": {
            "id": "ocr-extraction",
            "name": "OCR 텍스트 추출",
            "description": "eDOCr2를 사용한 치수 및 텍스트 추출",
            "category": "ocr",
            "drawing_type": "general",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "imageInput",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "이미지 입력"},
                },
                {
                    "id": "edocr2-1",
                    "type": "edocr2",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "eDOCr2 OCR",
                        "params": {
                            "language": "korean",
                            "extract_dimensions": True,
                            "extract_gdt": True,
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "edocr2-1"},
            ],
        },
        "full-analysis": {
            "id": "full-analysis",
            "name": "전체 분석 파이프라인",
            "description": "YOLO 검출 + OCR 추출 + 공차 분석",
            "category": "analysis",
            "drawing_type": "mechanical",
            "nodes": [
                {
                    "id": "input-1",
                    "type": "imageInput",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "이미지 입력"},
                },
                {
                    "id": "yolo-1",
                    "type": "yolo",
                    "position": {"x": 400, "y": 100},
                    "data": {
                        "label": "YOLO 검출",
                        "params": {
                            "model_type": "engineering",
                            "confidence": 0.5,
                        },
                    },
                },
                {
                    "id": "edocr2-1",
                    "type": "edocr2",
                    "position": {"x": 400, "y": 300},
                    "data": {
                        "label": "eDOCr2 OCR",
                        "params": {
                            "language": "korean",
                            "extract_dimensions": True,
                        },
                    },
                },
                {
                    "id": "skinmodel-1",
                    "type": "skinmodel",
                    "position": {"x": 700, "y": 200},
                    "data": {
                        "label": "공차 분석",
                        "params": {
                            "task": "tolerance_analysis",
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "input-1", "target": "yolo-1"},
                {"id": "e2", "source": "input-1", "target": "edocr2-1"},
                {"id": "e3", "source": "yolo-1", "target": "skinmodel-1"},
                {"id": "e4", "source": "edocr2-1", "target": "skinmodel-1"},
            ],
        },
    }
    return templates.get(template_id)
