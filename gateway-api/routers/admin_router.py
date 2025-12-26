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
    "line_detector": "line-detector-api",
    "line-detector": "line-detector-api",
    "pid_analyzer": "pid-analyzer-api",
    "pid-analyzer": "pid-analyzer-api",
    "design_checker": "design-checker-api",
    "design-checker": "design-checker-api",
    "tesseract": "tesseract-api",
    "trocr": "trocr-api",
    "esrgan": "esrgan-api",
    "ocr_ensemble": "ocr-ensemble-api",
    "ocr-ensemble": "ocr-ensemble-api",
    "knowledge": "knowledge-api",
    "blueprint-ai-bom": "blueprint-ai-bom-backend",
    "blueprint-ai-bom-backend": "blueprint-ai-bom-backend",
    "blueprint-ai-bom-frontend": "blueprint-ai-bom-frontend",
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
    """GPU 상태 조회 (nvidia-smi 사용, 호스트에서 실행 시도)"""
    # 먼저 직접 nvidia-smi 시도
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

    # Docker를 통해 GPU 정보 가져오기 시도 (호스트에서 실행)
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


# =============================================================================
# Result Management Endpoints (파이프라인 결과 저장/정리)
# =============================================================================

@admin_router.get("/results/stats")
async def get_result_statistics():
    """
    파이프라인 결과 저장소 통계
    - 총 용량, 파일 수, 날짜별 통계
    """
    try:
        from utils.result_manager import get_result_manager
        manager = get_result_manager()
        stats = manager.get_statistics()
        return stats
    except ImportError:
        raise HTTPException(status_code=501, detail="Result manager not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/results/recent")
async def get_recent_results(limit: int = 10):
    """
    최근 파이프라인 실행 결과 목록
    - limit: 조회할 개수 (기본 10)
    """
    try:
        from utils.result_manager import get_result_manager
        manager = get_result_manager()
        sessions = manager.list_recent_sessions(limit=limit)
        return {"sessions": sessions, "count": len(sessions)}
    except ImportError:
        raise HTTPException(status_code=501, detail="Result manager not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/results/cleanup")
async def cleanup_old_results(max_age_days: int = 7, dry_run: bool = False):
    """
    오래된 파이프라인 결과 정리
    - max_age_days: 보관 기간 (기본 7일)
    - dry_run: True면 실제 삭제 없이 목록만 반환
    """
    try:
        from utils.result_manager import get_result_manager
        manager = get_result_manager()
        result = manager.cleanup_old_results(max_age_days=max_age_days, dry_run=dry_run)
        return result
    except ImportError:
        raise HTTPException(status_code=501, detail="Result manager not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Container Configuration Endpoints (GPU/Memory 설정)
# =============================================================================

class ContainerConfigRequest(BaseModel):
    device: str = "cpu"  # "cpu" or "cuda"
    memory_limit: Optional[str] = None  # e.g., "4g"
    gpu_memory: Optional[str] = None  # e.g., "4g" (for GPU memory limit)


class ContainerConfigResponse(BaseModel):
    success: bool
    message: str
    service: str
    device: str
    recreated: bool


# docker-compose 경로 (호스트 경로)
DOCKER_COMPOSE_DIR = "/home/uproot/ax/poc"
DOCKER_COMPOSE_OVERRIDE = f"{DOCKER_COMPOSE_DIR}/docker-compose.override.yml"


def update_gpu_override(service_name: str, enable_gpu: bool, gpu_memory: Optional[str] = None) -> bool:
    """
    docker-compose.override.yml을 사용하여 서비스의 GPU 설정을 오버라이드합니다.
    원본 docker-compose.yml은 수정하지 않습니다.

    버그 수정 (2025-12-26):
    - GPU 비활성화 시 빈 배열로 오버라이드하여 원본 설정 무력화
    """
    import yaml

    try:
        # 기존 override 파일 읽기 또는 새로 생성
        override_data = {'services': {}}
        if os.path.exists(DOCKER_COMPOSE_OVERRIDE):
            with open(DOCKER_COMPOSE_OVERRIDE, 'r') as f:
                override_data = yaml.safe_load(f) or {'services': {}}
                if 'services' not in override_data:
                    override_data['services'] = {}

        if enable_gpu:
            # GPU 설정 추가
            deploy_config = {
                'deploy': {
                    'resources': {
                        'reservations': {
                            'devices': [{
                                'driver': 'nvidia',
                                'count': 1,
                                'capabilities': ['gpu']
                            }]
                        }
                    }
                }
            }

            # GPU 메모리 제한이 있으면 추가
            if gpu_memory:
                deploy_config['deploy']['resources']['limits'] = {
                    'memory': gpu_memory
                }

            override_data['services'][service_name] = deploy_config
            logger.info(f"GPU enabled for {service_name} in override file")
        else:
            # GPU 비활성화: 빈 devices 배열로 오버라이드하여 원본 GPU 설정 무력화
            # 단순히 삭제하면 원본 docker-compose.yml의 GPU 설정이 적용됨
            override_data['services'][service_name] = {
                'deploy': {
                    'resources': {
                        'reservations': {
                            'devices': []  # 빈 배열로 원본 GPU 설정 오버라이드
                        }
                    }
                }
            }
            logger.info(f"GPU disabled for {service_name} in override file (empty devices)")

        # override 파일 저장
        with open(DOCKER_COMPOSE_OVERRIDE, 'w') as f:
            yaml.dump(override_data, f, default_flow_style=False, allow_unicode=True)

        return True
    except Exception as e:
        logger.error(f"Failed to update docker-compose.override.yml: {e}")
        return False


def recreate_container(service_name: str) -> tuple[bool, str]:
    """
    Docker 컨테이너를 재생성합니다.
    docker:24.0-cli 이미지(Docker Compose v2 포함)를 사용하여 컨테이너를 재생성합니다.

    버그 수정 (2025-12-26):
    - stop/rm 결과 확인 및 로깅
    - --force-recreate 추가로 이름 충돌 방지
    - 잘못된 fallback 제거 (삭제된 컨테이너 start 시도 버그)
    """
    container_name = service_name

    try:
        # 1. 컨테이너 중지 (실패해도 계속 - 이미 중지된 경우)
        stop_result = subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        if stop_result.returncode != 0:
            logger.info(f"Container {container_name} stop skipped (may not be running): {stop_result.stderr.strip()}")
        else:
            logger.info(f"Container {container_name} stopped")

        # 2. 컨테이너 삭제 (실패해도 계속 - 존재하지 않는 경우)
        rm_result = subprocess.run(
            ["docker", "rm", container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if rm_result.returncode != 0:
            logger.info(f"Container {container_name} rm skipped (may not exist): {rm_result.stderr.strip()}")
        else:
            logger.info(f"Container {container_name} removed")

        # 3. docker:24.0-cli 이미지로 재생성 (Docker Compose v2 내장)
        # --force-recreate 추가: 이름 충돌 방지
        compose_result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", "/var/run/docker.sock:/var/run/docker.sock",
                "-v", f"{DOCKER_COMPOSE_DIR}:{DOCKER_COMPOSE_DIR}",
                "-w", DOCKER_COMPOSE_DIR,
                "docker:24.0-cli",
                "compose",
                "-f", f"{DOCKER_COMPOSE_DIR}/docker-compose.yml",
                "-f", DOCKER_COMPOSE_OVERRIDE,
                "up", "-d", "--force-recreate", service_name
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if compose_result.returncode == 0:
            logger.info(f"Container {container_name} recreated successfully")
            return True, f"Container {container_name} recreated with new settings"

        # compose 실패 시 에러 반환 (잘못된 fallback 제거)
        error_msg = compose_result.stderr.strip() or compose_result.stdout.strip() or 'Unknown error'
        logger.error(f"docker compose failed for {container_name}: {error_msg}")
        return False, f"Failed to recreate container: {error_msg}"

    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout while recreating {container_name}: {e}")
        return False, f"Timeout while recreating container (command: {e.cmd})"
    except Exception as e:
        logger.error(f"Exception while recreating {container_name}: {e}")
        return False, str(e)


class ContainerStatusResponse(BaseModel):
    service: str
    container_name: str
    running: bool
    gpu_enabled: bool
    gpu_count: int
    memory_limit: Optional[str] = None


@admin_router.get("/container/status/{service}", response_model=ContainerStatusResponse)
async def get_container_status(service: str):
    """
    컨테이너의 현재 GPU/메모리 상태를 조회합니다.
    """
    service_mapping = {
        "yolo": "yolo-api",
        "edocr2": "edocr2-v2-api",
        "edocr2-v2": "edocr2-v2-api",
        "paddleocr": "paddleocr-api",
        "edgnet": "edgnet-api",
        "skinmodel": "skinmodel-api",
        "vl": "vl-api",
        "line_detector": "line-detector-api",
        "line-detector": "line-detector-api",
        "pid_analyzer": "pid-analyzer-api",
        "pid-analyzer": "pid-analyzer-api",
        "design_checker": "design-checker-api",
        "design-checker": "design-checker-api",
        "tesseract": "tesseract-api",
        "trocr": "trocr-api",
        "esrgan": "esrgan-api",
        "ocr_ensemble": "ocr-ensemble-api",
        "ocr-ensemble": "ocr-ensemble-api",
        "surya_ocr": "surya-ocr-api",
        "surya-ocr": "surya-ocr-api",
        "doctr": "doctr-api",
        "easyocr": "easyocr-api",
        "gateway": "gateway-api",
        "blueprint-ai-bom": "blueprint-ai-bom-backend",
        "blueprint-ai-bom-backend": "blueprint-ai-bom-backend",
        "blueprint-ai-bom-frontend": "blueprint-ai-bom-frontend",
    }

    container_name = service_mapping.get(service, f"{service}-api")

    try:
        # docker inspect로 컨테이너 상태 조회
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format",
             '{{json .State.Running}}|||{{json .HostConfig.DeviceRequests}}|||{{json .HostConfig.Memory}}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"Container {container_name} not found")

        parts = result.stdout.strip().split("|||")
        running = parts[0].strip().lower() == "true"

        # GPU 상태 파싱
        import json
        gpu_enabled = False
        gpu_count = 0
        try:
            device_requests = json.loads(parts[1]) if parts[1] != "null" else []
            if device_requests:
                gpu_enabled = True
                gpu_count = len(device_requests)
        except:
            pass

        # 메모리 제한 파싱
        memory_limit = None
        try:
            memory_bytes = int(parts[2]) if parts[2] != "0" else 0
            if memory_bytes > 0:
                memory_gb = memory_bytes / (1024 ** 3)
                memory_limit = f"{memory_gb:.1f}g"
        except:
            pass

        return ContainerStatusResponse(
            service=service,
            container_name=container_name,
            running=running,
            gpu_enabled=gpu_enabled,
            gpu_count=gpu_count,
            memory_limit=memory_limit
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Timeout while inspecting container")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/container/configure/{service}", response_model=ContainerConfigResponse)
async def configure_container(service: str, config: ContainerConfigRequest):
    """
    컨테이너의 GPU/메모리 설정을 변경하고 재생성합니다.

    - service: 서비스 이름 (예: yolo, edocr2 등)
    - device: "cpu" 또는 "cuda"
    - memory_limit: 메모리 제한 (예: "4g")
    - gpu_memory: GPU 메모리 제한 (예: "4g")
    """
    # 서비스 이름을 docker-compose 서비스 이름으로 변환
    service_mapping = {
        "yolo": "yolo-api",
        "edocr2": "edocr2-v2-api",
        "edocr2-v2": "edocr2-v2-api",
        "paddleocr": "paddleocr-api",
        "edgnet": "edgnet-api",
        "skinmodel": "skinmodel-api",
        "vl": "vl-api",
        "line_detector": "line-detector-api",
        "line-detector": "line-detector-api",
        "pid_analyzer": "pid-analyzer-api",
        "pid-analyzer": "pid-analyzer-api",
        "design_checker": "design-checker-api",
        "design-checker": "design-checker-api",
        "tesseract": "tesseract-api",
        "trocr": "trocr-api",
        "esrgan": "esrgan-api",
        "ocr_ensemble": "ocr-ensemble-api",
        "ocr-ensemble": "ocr-ensemble-api",
        "surya_ocr": "surya-ocr-api",
        "surya-ocr": "surya-ocr-api",
        "doctr": "doctr-api",
        "easyocr": "easyocr-api",
    }

    compose_service_name = service_mapping.get(service, f"{service}-api")
    enable_gpu = config.device.lower() == "cuda"

    logger.info(f"Configuring {compose_service_name}: device={config.device}, gpu_memory={config.gpu_memory}")

    # 1. docker-compose.override.yml 업데이트
    if not update_gpu_override(compose_service_name, enable_gpu, config.gpu_memory):
        raise HTTPException(status_code=500, detail="Failed to update docker-compose.override.yml")

    # 2. 컨테이너 재생성
    success, message = recreate_container(compose_service_name)

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return ContainerConfigResponse(
        success=True,
        message=message,
        service=service,
        device=config.device,
        recreated=True
    )
