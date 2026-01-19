"""
Admin Router - 시스템 관리 API
- 시스템 현황 (API 상태, GPU, CPU/Memory/Disk)
- 모델 파일 목록

Gateway Registry와 통합되어 동적으로 API 목록을 관리

관련 라우터:
- docker_router.py: Docker 컨테이너 제어
- results_router.py: 파이프라인 결과 관리
- gpu_config_router.py: GPU 설정
- api_key_router.py: API 키 관리
"""

import os
import time
import subprocess
import logging
from datetime import datetime
from typing import List, Optional

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


# 모델 디렉토리 (docker-compose에서 마운트된 경로)
MODEL_DIRS = {
    "yolo": {
        "container": "/app/admin_models/yolo",
        "host": "/home/uproot/ax/poc/models/yolo-api/models"
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


class ModelFilesResponse(BaseModel):
    model_type: str
    host_path: str
    file_count: int
    total_size_mb: float


# =============================================================================
# Helper Functions
# =============================================================================

async def check_api_health(service: dict) -> APIStatus:
    """API 헬스체크 수행"""
    start_time = time.time()
    status = "unknown"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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
    # 직접 nvidia-smi 시도
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
        logger.debug(f"Direct nvidia-smi failed: {e}")

    # Docker를 통해 GPU 정보 가져오기 시도
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--gpus", "all", "--entrypoint", "nvidia-smi",
             "nvidia/cuda:12.0.0-base-ubuntu22.04",
             "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=30
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
        logger.debug(f"Docker nvidia-smi failed: {e}")

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


def _count_model_files(paths: list) -> tuple[int, int]:
    """모델 파일 수와 총 크기 계산"""
    file_count = 0
    total_size = 0

    for path in paths:
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

    return file_count, total_size


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
            api_statuses.append(APIStatus(
                name=api_meta.id,
                display_name=api_meta.display_name,
                status=api_meta.status or "unknown",
                response_time=0.0,
                port=api_meta.port,
                gpu_enabled=api_meta.category in ["detection", "ocr", "segmentation"]
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

    return SystemStatusResponse(
        apis=api_statuses,
        gpu=get_gpu_status(),
        system=get_system_resources(),
        timestamp=datetime.now().isoformat()
    )


@admin_router.get("/models", response_model=List[ModelFilesResponse])
async def get_all_models():
    """모든 모델 경로 조회"""
    results = []
    for model_type, model_info in MODEL_DIRS.items():
        file_count, total_size = _count_model_files([
            model_info["container"],
            model_info["host"]
        ])

        results.append(ModelFilesResponse(
            model_type=model_type,
            host_path=model_info["host"],
            file_count=file_count,
            total_size_mb=round(total_size / (1024 * 1024), 2)
        ))

    return results


@admin_router.get("/models/{model_type}", response_model=ModelFilesResponse)
async def get_model_files(model_type: str):
    """모델 경로 조회 (yolo, edocr2, edocr2-v2, edgnet, skinmodel)"""
    if model_type not in MODEL_DIRS:
        raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")

    model_info = MODEL_DIRS[model_type]
    file_count, total_size = _count_model_files([
        model_info["container"],
        model_info["host"]
    ])

    return ModelFilesResponse(
        model_type=model_type,
        host_path=model_info["host"],
        file_count=file_count,
        total_size_mb=round(total_size / (1024 * 1024), 2)
    )
