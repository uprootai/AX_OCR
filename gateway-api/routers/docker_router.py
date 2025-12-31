"""
Docker Router - Docker 컨테이너 제어 및 모니터링
- Docker 컨테이너 start/stop/restart
- Docker 로그 조회
- 실행 중인 컨테이너 목록
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from constants import get_container_name
from utils.subprocess_utils import (
    run_docker_command,
    get_docker_logs,
    get_docker_containers as _get_docker_containers
)

logger = logging.getLogger(__name__)

docker_router = APIRouter(prefix="/admin", tags=["Docker"])


# =============================================================================
# Response Models
# =============================================================================

class DockerActionResponse(BaseModel):
    success: bool
    message: str
    service: str
    action: str


class LogsResponse(BaseModel):
    service: str
    logs: str
    lines: int


class ContainerInfo(BaseModel):
    name: str
    status: str
    ports: str


class DockerContainerList(BaseModel):
    """Docker 컨테이너 목록 (docker_router 전용)"""
    containers: List[ContainerInfo]


# =============================================================================
# API Endpoints
# =============================================================================

@docker_router.post("/docker/{action}/{service}", response_model=DockerActionResponse)
async def docker_control(action: str, service: str):
    """
    Docker 컨테이너 제어
    - action: start, stop, restart
    - service: gateway, yolo, edocr2, paddleocr, edgnet, skinmodel, vl, etc.
    """
    container_name = get_container_name(service)

    success, message = run_docker_command(action, container_name)

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return DockerActionResponse(
        success=success,
        message=message,
        service=service,
        action=action
    )


@docker_router.get("/logs/{service}", response_model=LogsResponse)
async def get_service_logs(service: str, lines: int = 200):
    """
    Docker 서비스 로그 조회
    - service: gateway, yolo, edocr2, paddleocr, edgnet, skinmodel, vl, etc.
    - lines: 조회할 로그 줄 수 (기본 200)
    """
    container_name = get_container_name(service)

    logs = get_docker_logs(container_name, lines)

    return LogsResponse(
        service=service,
        logs=logs,
        lines=lines
    )


@docker_router.get("/docker/ps")
async def get_docker_containers_endpoint():
    """
    실행 중인 Docker 컨테이너 목록
    """
    try:
        containers_data = _get_docker_containers()
        containers = [
            ContainerInfo(
                name=c["name"],
                status=c["status"],
                ports=c["ports"]
            )
            for c in containers_data
        ]
        return DockerContainerList(containers=containers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
