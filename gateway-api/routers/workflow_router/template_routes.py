"""
Template-based Workflow Routes (P2-2)
BOM API 연동 템플릿 조회 및 템플릿 기반 워크플로우 실행 엔드포인트
"""

import json
import base64
import logging
import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
import httpx

from blueprintflow import WorkflowDefinition

from .builtin_templates import get_builtin_templates, get_builtin_template
from .core_routes import blueprint_engine

logger = logging.getLogger(__name__)

# Blueprint AI BOM API URL (템플릿 관리)
BOM_API_URL = os.getenv("BOM_API_URL", "http://localhost:5020")

router = APIRouter()


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
        builtin = get_builtin_templates()
        return {
            "status": "fallback",
            "templates": builtin,
            "total": len(builtin),
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
                builtin = get_builtin_template(template_id)
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
        builtin = get_builtin_template(template_id)
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
