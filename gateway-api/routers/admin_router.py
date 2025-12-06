"""
Admin Router - 시스템 관리 API
- 시스템 현황 (API 상태, GPU, CPU/Memory/Disk)
- 모델 파일 목록
- Docker 컨테이너 제어
- 서비스 로그 조회

Gateway Registry와 통합되어 동적으로 API 목록을 관리
"""

import os
import time
import asyncio
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# API Registry 참조 (api_server.py에서 설정됨)
_api_registry = None

def set_api_registry(registry):
    """API Registry 인스턴스 설정 (api_server.py에서 호출)"""
    global _api_registry
    _api_registry = registry
    logger.info("Admin router: API Registry 연결됨")

def get_api_registry():
    """API Registry 인스턴스 반환"""
    return _api_registry

# Docker 서비스 이름 매핑 (컨테이너 이름)
DOCKER_SERVICE_MAPPING = {
    "gateway": "gateway-api",
    "yolo": "yolo-api",
    "edocr2": "edocr2-api",
    "edocr2-v1": "edocr2-api",
    "edocr2-v2": "edocr2-v2-api",
    "paddleocr": "paddleocr-api",
    "surya-ocr": "surya-ocr-api",
    "doctr": "doctr-api",
    "easyocr": "easyocr-api",
    "edgnet": "edgnet-api",
    "skinmodel": "skinmodel-api",
    "vl": "vl-api",
}

# 모델 디렉토리 (docker-compose에서 마운트된 경로)
# 호스트 경로: /home/uproot/ax/poc/models/{api}-api/models
MODEL_DIRS = {
    "yolo": {
        "container": "/app/admin_models/yolo",
        "host": "/home/uproot/ax/poc/models/yolo-api/models"
    },
    "edocr2": {
        "container": "/app/admin_models/edocr2",
        "host": "/home/uproot/ax/poc/models/edocr2-api/models"
    },
    "edocr2-v2": {
        "container": "/app/admin_models/edocr2-v2",
        "host": "/home/uproot/ax/poc/models/edocr2-v2-api/models"
    },
    "edgnet": {
        "container": "/app/admin_models/edgnet",
        "host": "/home/uproot/ax/poc/models/edgnet-api/models"
    },
    "skinmodel": {
        "container": "/app/admin_models/skinmodel",
        "host": "/home/uproot/ax/poc/models/skinmodel-api/models"
    },
}

# =============================================================================
# Response Models
# =============================================================================

class APIStatus(BaseModel):
    name: str
    display_name: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time: float
    port: int
    gpu_enabled: bool

class GPUStatus(BaseModel):
    available: bool
    device_name: Optional[str] = None
    total_memory: Optional[int] = None
    used_memory: Optional[int] = None
    free_memory: Optional[int] = None
    utilization: Optional[int] = None

class SystemResources(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float

class SystemStatusResponse(BaseModel):
    apis: List[APIStatus]
    gpu: GPUStatus
    system: SystemResources
    timestamp: str

class ModelFile(BaseModel):
    name: str
    size: int
    modified: Optional[str] = None

class ModelFilesResponse(BaseModel):
    model_type: str
    host_path: str  # 호스트 절대 경로
    file_count: int  # 파일 개수
    total_size_mb: float  # 총 크기 (MB)

class DockerActionResponse(BaseModel):
    success: bool
    message: str
    service: str
    action: str

class LogsResponse(BaseModel):
    service: str
    logs: str
    lines: int

# =============================================================================
# Helper Functions
# =============================================================================

async def check_api_health(service: dict) -> APIStatus:
    """API 헬스체크 수행"""
    start_time = time.time()
    status = "unknown"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # /health 또는 /api/v1/health 시도
            for endpoint in ["/health", "/api/v1/health"]:
                try:
                    response = await client.get(f"{service['url']}{endpoint}")
                    if response.status_code == 200:
                        status = "healthy"
                        break
                except:
                    continue

            if status == "unknown":
                status = "unhealthy"
    except Exception as e:
        logger.debug(f"Health check failed for {service['name']}: {e}")
        status = "unhealthy"

    response_time = time.time() - start_time

    return APIStatus(
        name=service["name"],
        display_name=service["display_name"],
        status=status,
        response_time=response_time,
        port=service["port"],
        gpu_enabled=service["gpu"]
    )

def get_gpu_status() -> GPUStatus:
    """GPU 상태 조회 (nvidia-smi 사용)"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 5:
                return GPUStatus(
                    available=True,
                    device_name=parts[0],
                    total_memory=int(float(parts[1])),
                    used_memory=int(float(parts[2])),
                    free_memory=int(float(parts[3])),
                    utilization=int(float(parts[4]))
                )
    except Exception as e:
        logger.debug(f"GPU status check failed: {e}")

    return GPUStatus(available=False)

def get_system_resources() -> SystemResources:
    """시스템 리소스 조회"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return SystemResources(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        memory_used_gb=round(memory.used / (1024 ** 3), 2),
        memory_total_gb=round(memory.total / (1024 ** 3), 2),
        disk_percent=disk.percent,
        disk_used_gb=round(disk.used / (1024 ** 3), 2),
        disk_total_gb=round(disk.total / (1024 ** 3), 2)
    )

def run_docker_command(action: str, container_name: str) -> tuple[bool, str]:
    """Docker 명령어 실행"""
    valid_actions = ["start", "stop", "restart"]
    if action not in valid_actions:
        return False, f"Invalid action: {action}. Must be one of {valid_actions}"

    try:
        result = subprocess.run(
            ["docker", action, container_name],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return True, f"Successfully {action}ed {container_name}"
        else:
            return False, result.stderr or f"Failed to {action} {container_name}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout while {action}ing {container_name}"
    except Exception as e:
        return False, str(e)

def get_docker_logs(container_name: str, lines: int = 200) -> str:
    """Docker 로그 조회"""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_name],
            capture_output=True,
            text=True,
            timeout=30
        )

        # stdout과 stderr를 합침
        logs = result.stdout + result.stderr
        return logs if logs else "No logs available"
    except subprocess.TimeoutExpired:
        return "Timeout while fetching logs"
    except Exception as e:
        return f"Error fetching logs: {e}"

# =============================================================================
# API Endpoints
# =============================================================================

@admin_router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    시스템 전체 상태 조회
    - Gateway Registry에서 동적으로 API 목록 가져옴
    - GPU 상태
    - CPU/Memory/Disk 사용량
    """
    api_statuses = []

    # Gateway Registry에서 API 목록 가져오기
    registry = get_api_registry()
    if registry and hasattr(registry, 'apis'):
        for api_id, api_meta in registry.apis.items():
            # Registry의 API 정보를 Admin 형식으로 변환
            api_statuses.append(APIStatus(
                name=api_meta.id,
                display_name=api_meta.display_name,
                status=api_meta.status or "unknown",
                response_time=0.0,  # Registry에서 직접 가져오므로 응답시간 불필요
                port=api_meta.port,
                gpu_enabled=api_meta.category in ["detection", "ocr", "segmentation"]  # 카테고리 기반 추정
            ))

    # Gateway 자체도 추가 (항상 healthy)
    gateway_exists = any(api.name == "gateway" for api in api_statuses)
    if not gateway_exists:
        api_statuses.insert(0, APIStatus(
            name="gateway",
            display_name="Gateway API",
            status="healthy",
            response_time=0.0,
            port=8000,
            gpu_enabled=False
        ))

    # GPU 상태
    gpu_status = get_gpu_status()

    # 시스템 리소스
    system_resources = get_system_resources()

    return SystemStatusResponse(
        apis=api_statuses,
        gpu=gpu_status,
        system=system_resources,
        timestamp=datetime.now().isoformat()
    )

@admin_router.get("/models", response_model=List[ModelFilesResponse])
async def get_all_models():
    """
    모든 모델 경로 조회
    """
    results = []
    for model_type, model_info in MODEL_DIRS.items():
        container_dir = model_info["container"]
        host_path = model_info["host"]

        file_count = 0
        total_size = 0

        for path in [container_dir, host_path]:
            if os.path.exists(path):
                try:
                    for f in os.listdir(path):
                        filepath = os.path.join(path, f)
                        if os.path.isfile(filepath) and not f.endswith('.py'):
                            file_count += 1
                            total_size += os.stat(filepath).st_size
                    break
                except Exception as e:
                    logger.error(f"Error listing model files: {e}")

        results.append(ModelFilesResponse(
            model_type=model_type,
            host_path=host_path,
            file_count=file_count,
            total_size_mb=round(total_size / (1024 * 1024), 2)
        ))

    return results

@admin_router.get("/models/{model_type}", response_model=ModelFilesResponse)
async def get_model_files(model_type: str):
    """
    모델 경로 조회
    - yolo, edocr2, edocr2-v2, edgnet, skinmodel
    """
    if model_type not in MODEL_DIRS:
        raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")

    model_info = MODEL_DIRS[model_type]
    container_dir = model_info["container"]
    host_path = model_info["host"]

    file_count = 0
    total_size = 0

    # 컨테이너 경로로 시도
    check_paths = [container_dir, host_path]

    for path in check_paths:
        if os.path.exists(path):
            try:
                for f in os.listdir(path):
                    filepath = os.path.join(path, f)
                    if os.path.isfile(filepath) and not f.endswith('.py'):
                        file_count += 1
                        total_size += os.stat(filepath).st_size
                break
            except Exception as e:
                logger.error(f"Error listing model files: {e}")

    return ModelFilesResponse(
        model_type=model_type,
        host_path=host_path,
        file_count=file_count,
        total_size_mb=round(total_size / (1024 * 1024), 2)
    )

@admin_router.post("/docker/{action}/{service}", response_model=DockerActionResponse)
async def docker_control(action: str, service: str):
    """
    Docker 컨테이너 제어
    - action: start, stop, restart
    - service: gateway, yolo, edocr2, paddleocr, edgnet, skinmodel, vl, etc.
    """
    container_name = DOCKER_SERVICE_MAPPING.get(service, f"{service}-api")

    success, message = run_docker_command(action, container_name)

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return DockerActionResponse(
        success=success,
        message=message,
        service=service,
        action=action
    )

@admin_router.get("/logs/{service}", response_model=LogsResponse)
async def get_service_logs(service: str, lines: int = 200):
    """
    Docker 서비스 로그 조회
    - service: gateway, yolo, edocr2, paddleocr, edgnet, skinmodel, vl, etc.
    - lines: 조회할 로그 줄 수 (기본 200)
    """
    container_name = DOCKER_SERVICE_MAPPING.get(service, f"{service}-api")

    logs = get_docker_logs(container_name, lines)

    return LogsResponse(
        service=service,
        logs=logs,
        lines=lines
    )

@admin_router.get("/docker/ps")
async def get_docker_containers():
    """
    실행 중인 Docker 컨테이너 목록
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )

        containers = []
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        containers.append({
                            "name": parts[0],
                            "status": parts[1],
                            "ports": parts[2] if len(parts) > 2 else ""
                        })

        return {"containers": containers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
