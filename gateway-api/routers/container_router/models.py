"""
Container Router - Shared models, state, and Docker client
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ThreadPoolExecutor for blocking Docker SDK calls
_docker_executor = ThreadPoolExecutor(max_workers=4)

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


class ContainerStatusInfo(BaseModel):
    """경량 컨테이너 상태 정보 (stats 없이)"""
    name: str
    status: str


class ContainerStatusResponse(BaseModel):
    success: bool
    containers: List[ContainerStatusInfo]
    error: Optional[str] = None


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
