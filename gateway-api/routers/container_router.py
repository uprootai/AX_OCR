"""
Container Management Router
Docker 컨테이너 상태 조회 및 시작/중지 API
"""
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ThreadPoolExecutor for blocking Docker SDK calls
_docker_executor = ThreadPoolExecutor(max_workers=4)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/containers", tags=["containers"])

# 컨테이너 상태 캐시 (5초간 유효)
_container_status_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": 0,
    "ttl": 5  # 5초 캐시
}

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


class ContainerStatusInfo(BaseModel):
    """경량 컨테이너 상태 정보 (stats 없이)"""
    name: str
    status: str


class ContainerStatusResponse(BaseModel):
    success: bool
    containers: List[ContainerStatusInfo]
    error: Optional[str] = None


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


@router.get("/status", response_model=ContainerStatusResponse)
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
        # Docker SDK 호출을 ThreadPool에서 비동기로 실행 (이벤트 루프 블로킹 방지)
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


@router.get("", response_model=ContainerListResponse)
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
    except docker.errors.NotFound:
        return ContainerActionResponse(
            success=False,
            message=f"Container '{container_name}' not found",
            error="not_found"
        )
    except Exception as e:
        logger.error(f"Failed to start container {container_name}: {e}")
        return ContainerActionResponse(
            success=False,
            message=f"Failed to start container",
            error=str(e)
        )


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
    except docker.errors.NotFound:
        return ContainerActionResponse(
            success=False,
            message=f"Container '{container_name}' not found",
            error="not_found"
        )
    except Exception as e:
        logger.error(f"Failed to stop container {container_name}: {e}")
        return ContainerActionResponse(
            success=False,
            message=f"Failed to stop container",
            error=str(e)
        )


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
    except docker.errors.NotFound:
        return ContainerActionResponse(
            success=False,
            message=f"Container '{container_name}' not found",
            error="not_found"
        )
    except Exception as e:
        logger.error(f"Failed to restart container {container_name}: {e}")
        return ContainerActionResponse(
            success=False,
            message=f"Failed to restart container",
            error=str(e)
        )


@router.post("/{container_name}/start", response_model=ContainerActionResponse)
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


@router.post("/{container_name}/stop", response_model=ContainerActionResponse)
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


@router.post("/{container_name}/restart", response_model=ContainerActionResponse)
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


class GPUInfo(BaseModel):
    index: int
    name: str
    memory_used: int  # MB
    memory_total: int  # MB
    memory_percent: float
    utilization: float  # GPU utilization %
    temperature: Optional[int] = None  # Celsius


class GPUStatsResponse(BaseModel):
    success: bool
    available: bool
    gpus: List[GPUInfo]
    error: Optional[str] = None


@router.get("/gpu/stats", response_model=GPUStatsResponse)
async def get_gpu_stats():
    """GPU 사용량 조회 (nvidia-smi)"""
    import subprocess

    def try_nvidia_smi():
        """Try to run nvidia-smi directly or via docker"""
        # 방법 1: 직접 nvidia-smi 실행 시도
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 방법 2: GPU가 있는 다른 컨테이너를 통해 실행 시도
        if DOCKER_AVAILABLE:
            gpu_containers = ['yolo-api', 'edocr2-v2-api', 'esrgan-api', 'edgnet-api']
            for container_name in gpu_containers:
                try:
                    container = docker_client.containers.get(container_name)
                    if container.status == 'running':
                        exec_result = container.exec_run(
                            "nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits",
                            demux=True
                        )
                        if exec_result.exit_code == 0 and exec_result.output[0]:
                            return exec_result.output[0].decode('utf-8')
                except Exception:
                    continue

        return None

    try:
        output = try_nvidia_smi()

        if output is None:
            return GPUStatsResponse(
                success=True,
                available=False,
                gpus=[],
                error="nvidia-smi not found (no NVIDIA GPU or no running GPU container)"
            )

        gpus = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                mem_used = int(parts[2])
                mem_total = int(parts[3])
                gpus.append(GPUInfo(
                    index=int(parts[0]),
                    name=parts[1],
                    memory_used=mem_used,
                    memory_total=mem_total,
                    memory_percent=round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0,
                    utilization=float(parts[4]),
                    temperature=int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else None
                ))

        return GPUStatsResponse(
            success=True,
            available=len(gpus) > 0,
            gpus=gpus
        )

    except Exception as e:
        logger.error(f"Failed to get GPU stats: {e}")
        return GPUStatsResponse(
            success=False,
            available=False,
            gpus=[],
            error=str(e)
        )
