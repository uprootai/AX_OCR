"""
Container Management Router
Docker 컨테이너 상태 조회 및 시작/중지 API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/containers", tags=["containers"])

# Docker SDK 동적 로드
try:
    import docker
    docker_client = docker.from_env()
    DOCKER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Docker SDK not available: {e}")
    docker_client = None
    DOCKER_AVAILABLE = False


class ContainerInfo(BaseModel):
    id: str
    name: str
    status: str
    image: str
    ports: dict
    created: str
    memory_usage: Optional[str] = None
    cpu_percent: Optional[float] = None


class ContainerListResponse(BaseModel):
    success: bool
    containers: List[ContainerInfo]
    error: Optional[str] = None


class ContainerActionResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None


def format_memory(mem_bytes: int) -> str:
    """바이트를 읽기 쉬운 형식으로 변환"""
    if mem_bytes < 1024:
        return f"{mem_bytes}B"
    elif mem_bytes < 1024 * 1024:
        return f"{mem_bytes / 1024:.1f}KB"
    elif mem_bytes < 1024 * 1024 * 1024:
        return f"{mem_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{mem_bytes / (1024 * 1024 * 1024):.2f}GB"


@router.get("", response_model=ContainerListResponse)
async def list_containers():
    """모든 Docker 컨테이너 목록 조회"""
    if not DOCKER_AVAILABLE:
        return ContainerListResponse(
            success=False,
            containers=[],
            error="Docker SDK not available"
        )

    try:
        containers = docker_client.containers.list(all=True)
        container_list = []

        for c in containers:
            # 포트 매핑 추출
            ports = {}
            if c.attrs.get("NetworkSettings", {}).get("Ports"):
                for port, bindings in c.attrs["NetworkSettings"]["Ports"].items():
                    if bindings:
                        ports[port] = bindings[0].get("HostPort", "")

            # 메모리 사용량 (running 상태일 때만)
            memory_usage = None
            cpu_percent = None
            if c.status == "running":
                try:
                    stats = c.stats(stream=False)
                    # 메모리 계산
                    mem_stats = stats.get("memory_stats", {})
                    if "usage" in mem_stats:
                        memory_usage = format_memory(mem_stats["usage"])

                    # CPU 계산
                    cpu_stats = stats.get("cpu_stats", {})
                    precpu_stats = stats.get("precpu_stats", {})
                    if cpu_stats and precpu_stats:
                        cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - \
                                    precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                        system_delta = cpu_stats.get("system_cpu_usage", 0) - \
                                       precpu_stats.get("system_cpu_usage", 0)
                        if system_delta > 0:
                            num_cpus = cpu_stats.get("online_cpus", 1)
                            cpu_percent = round((cpu_delta / system_delta) * num_cpus * 100, 1)
                except Exception:
                    pass

            container_list.append(ContainerInfo(
                id=c.short_id,
                name=c.name,
                status=c.status,
                image=c.image.tags[0] if c.image.tags else c.image.short_id,
                ports=ports,
                created=c.attrs.get("Created", "")[:19],
                memory_usage=memory_usage,
                cpu_percent=cpu_percent,
            ))

        # poc_ 또는 api 관련 컨테이너만 필터링
        filtered = [c for c in container_list if
                    'poc' in c.image.lower() or
                    'api' in c.name.lower() or
                    'web-ui' in c.name.lower() or
                    'neo4j' in c.name.lower()]

        return ContainerListResponse(
            success=True,
            containers=sorted(filtered, key=lambda x: x.name)
        )

    except Exception as e:
        logger.error(f"Failed to list containers: {e}")
        return ContainerListResponse(
            success=False,
            containers=[],
            error=str(e)
        )


@router.post("/{container_name}/start", response_model=ContainerActionResponse)
async def start_container(container_name: str):
    """컨테이너 시작"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Docker SDK not available")

    try:
        container = docker_client.containers.get(container_name)
        if container.status == "running":
            return ContainerActionResponse(
                success=True,
                message=f"Container '{container_name}' is already running"
            )

        container.start()
        return ContainerActionResponse(
            success=True,
            message=f"Container '{container_name}' started successfully"
        )
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except Exception as e:
        logger.error(f"Failed to start container {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{container_name}/stop", response_model=ContainerActionResponse)
async def stop_container(container_name: str):
    """컨테이너 중지"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Docker SDK not available")

    try:
        container = docker_client.containers.get(container_name)
        if container.status != "running":
            return ContainerActionResponse(
                success=True,
                message=f"Container '{container_name}' is already stopped"
            )

        container.stop(timeout=10)
        return ContainerActionResponse(
            success=True,
            message=f"Container '{container_name}' stopped successfully"
        )
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except Exception as e:
        logger.error(f"Failed to stop container {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{container_name}/restart", response_model=ContainerActionResponse)
async def restart_container(container_name: str):
    """컨테이너 재시작"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Docker SDK not available")

    try:
        container = docker_client.containers.get(container_name)
        container.restart(timeout=10)
        return ContainerActionResponse(
            success=True,
            message=f"Container '{container_name}' restarted successfully"
        )
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
    except Exception as e:
        logger.error(f"Failed to restart container {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
