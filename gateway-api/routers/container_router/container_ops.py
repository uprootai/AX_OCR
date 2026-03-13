"""
Container Router - Container list, status, start, stop, restart operations
Route registration is handled by the package __init__.py (barrel).
"""
import asyncio
import logging
import time
from fastapi import HTTPException

from .models import (
    ContainerInfo,
    ContainerListResponse,
    ContainerActionResponse,
    ContainerStatusInfo,
    ContainerStatusResponse,
    DOCKER_AVAILABLE,
    _docker_executor,
    _container_status_cache,
    docker_client,
    format_memory,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sync helpers (run inside ThreadPoolExecutor)
# ---------------------------------------------------------------------------

def _get_container_status_sync() -> ContainerStatusResponse:
    """동기 방식으로 컨테이너 상태 조회 (ThreadPool에서 실행)"""
    try:
        containers = docker_client.containers.list(all=True)
        container_list = []

        for c in containers:
            # poc_ 또는 api 관련 컨테이너만 필터링 (컨테이너 이름 기반)
            try:
                image_name = c.image.tags[0] if c.image.tags else ""
            except Exception:
                image_name = ""

            if not ('poc' in image_name.lower() or
                    'api' in c.name.lower() or
                    'web-ui' in c.name.lower() or
                    'neo4j' in c.name.lower() or
                    'gateway' in c.name.lower() or
                    'blueprint' in c.name.lower()):
                continue

            container_list.append(ContainerStatusInfo(
                name=c.name,
                status=c.status,
            ))

        return ContainerStatusResponse(
            success=True,
            containers=sorted(container_list, key=lambda x: x.name)
        )
    except Exception as e:
        logger.error(f"Failed to list container status: {e}")
        return ContainerStatusResponse(
            success=False,
            containers=[],
            error=str(e)
        )


def _list_containers_sync(include_stats: bool = False) -> ContainerListResponse:
    """동기 방식으로 컨테이너 목록 조회 (ThreadPool에서 실행)

    Args:
        include_stats: True면 CPU/메모리 통계 포함 (느림), False면 기본 정보만 (빠름)
    """
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

            # 메모리 사용량 (include_stats=True이고 running 상태일 때만)
            memory_usage = None
            cpu_percent = None
            if include_stats and c.status == "running":
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
                except Exception as e:
                    logger.debug(f"CPU 사용률 계산 실패 (컨테이너 stats 미지원): {e}")

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
                    'neo4j' in c.name.lower() or
                    'blueprint' in c.name.lower()]

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


def _is_not_found(e: Exception) -> bool:
    """docker.errors.NotFound 여부 확인 (docker SDK 선택적 임포트 대응)"""
    try:
        import docker as _docker
        return isinstance(e, _docker.errors.NotFound)
    except ImportError:
        return False


def _not_found_response(container_name: str) -> ContainerActionResponse:
    return ContainerActionResponse(
        success=False,
        message=f"Container '{container_name}' not found",
        error="not_found"
    )


def _start_container_sync(container_name: str) -> ContainerActionResponse:
    """동기 방식으로 컨테이너 시작 (ThreadPool에서 실행)"""
    global _container_status_cache
    try:
        container = docker_client.containers.get(container_name)
        if container.status == "running":
            return ContainerActionResponse(
                success=True,
                message=f"Container '{container_name}' is already running"
            )
        container.start()
        _container_status_cache["data"] = None
        return ContainerActionResponse(
            success=True,
            message=f"Container '{container_name}' started successfully"
        )
    except Exception as e:
        if _is_not_found(e):
            return _not_found_response(container_name)
        logger.error(f"Failed to start container {container_name}: {e}")
        return ContainerActionResponse(success=False, message="Failed to start container", error=str(e))


def _stop_container_sync(container_name: str) -> ContainerActionResponse:
    """동기 방식으로 컨테이너 중지 (ThreadPool에서 실행)"""
    global _container_status_cache
    try:
        container = docker_client.containers.get(container_name)
        if container.status != "running":
            return ContainerActionResponse(
                success=True,
                message=f"Container '{container_name}' is already stopped"
            )
        container.stop(timeout=10)
        _container_status_cache["data"] = None
        return ContainerActionResponse(
            success=True,
            message=f"Container '{container_name}' stopped successfully"
        )
    except Exception as e:
        if _is_not_found(e):
            return _not_found_response(container_name)
        logger.error(f"Failed to stop container {container_name}: {e}")
        return ContainerActionResponse(success=False, message="Failed to stop container", error=str(e))


def _restart_container_sync(container_name: str) -> ContainerActionResponse:
    """동기 방식으로 컨테이너 재시작 (ThreadPool에서 실행)"""
    global _container_status_cache
    try:
        container = docker_client.containers.get(container_name)
        container.restart(timeout=10)
        _container_status_cache["data"] = None
        return ContainerActionResponse(
            success=True,
            message=f"Container '{container_name}' restarted successfully"
        )
    except Exception as e:
        if _is_not_found(e):
            return _not_found_response(container_name)
        logger.error(f"Failed to restart container {container_name}: {e}")
        return ContainerActionResponse(success=False, message="Failed to restart container", error=str(e))


# ---------------------------------------------------------------------------
# Route handlers (registered via __init__.py barrel)
# ---------------------------------------------------------------------------

async def list_container_status():
    """컨테이너 상태만 빠르게 조회 (실행 전 체크용, stats 수집 없음, 5초 캐시)"""
    global _container_status_cache

    # 캐시 확인
    now = time.time()
    if (_container_status_cache["data"] is not None and
        now - _container_status_cache["timestamp"] < _container_status_cache["ttl"]):
        return _container_status_cache["data"]

    if not DOCKER_AVAILABLE:
        return ContainerStatusResponse(
            success=False,
            containers=[],
            error="Docker SDK not available"
        )

    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(_docker_executor, _get_container_status_sync),
            timeout=5.0  # 5초 타임아웃
        )

        # 캐시 저장
        _container_status_cache["data"] = response
        _container_status_cache["timestamp"] = now

        return response

    except asyncio.TimeoutError:
        logger.error("Container status check timed out")
        return ContainerStatusResponse(
            success=False,
            containers=[],
            error="Container status check timed out"
        )
    except Exception as e:
        logger.error(f"Failed to list container status: {e}")
        return ContainerStatusResponse(
            success=False,
            containers=[],
            error=str(e)
        )


async def list_containers(include_stats: bool = False):
    """모든 Docker 컨테이너 목록 조회 (상세 정보 포함, Dashboard용)

    Args:
        include_stats: CPU/메모리 통계 포함 여부 (기본: False, 느림)
    """
    if not DOCKER_AVAILABLE:
        return ContainerListResponse(
            success=False,
            containers=[],
            error="Docker SDK not available"
        )

    try:
        loop = asyncio.get_event_loop()
        # stats 포함 시 30초, 미포함 시 10초 타임아웃
        timeout = 30.0 if include_stats else 10.0
        response = await asyncio.wait_for(
            loop.run_in_executor(
                _docker_executor,
                lambda: _list_containers_sync(include_stats)
            ),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.error(f"Container list timeout ({timeout}s)")
        return ContainerListResponse(
            success=False,
            containers=[],
            error="Container list timeout"
        )
    except Exception as e:
        logger.error(f"Failed to list containers: {e}")
        return ContainerListResponse(
            success=False,
            containers=[],
            error=str(e)
        )


async def start_container(container_name: str):
    """컨테이너 시작"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Docker SDK not available")

    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(_docker_executor, _start_container_sync, container_name),
            timeout=30.0
        )
        if response.error == "not_found":
            raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
        return response
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Container start timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stop_container(container_name: str):
    """컨테이너 중지"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Docker SDK not available")

    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(_docker_executor, _stop_container_sync, container_name),
            timeout=30.0
        )
        if response.error == "not_found":
            raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
        return response
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Container stop timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def restart_container(container_name: str):
    """컨테이너 재시작"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=500, detail="Docker SDK not available")

    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(_docker_executor, _restart_container_sync, container_name),
            timeout=30.0
        )
        if response.error == "not_found":
            raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
        return response
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Container restart timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart container {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
