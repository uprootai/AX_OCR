"""
GPU Configuration Router

컨테이너 GPU/메모리 설정 변경 및 재생성 API
분리: admin_router.py (2025-12-31)
"""

import os
import subprocess
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from constants import DOCKER_SERVICE_MAPPING

logger = logging.getLogger(__name__)

gpu_config_router = APIRouter(prefix="/admin", tags=["Admin - GPU Config"])

# =============================================================================
# Constants
# =============================================================================

# docker-compose 경로 (호스트 경로)
DOCKER_COMPOSE_DIR = "/home/uproot/ax/poc"
DOCKER_COMPOSE_OVERRIDE = f"{DOCKER_COMPOSE_DIR}/docker-compose.override.yml"

# 공통 상수 사용 (constants/docker_services.py에서 import)
SERVICE_MAPPING = DOCKER_SERVICE_MAPPING


# =============================================================================
# Request/Response Models
# =============================================================================

class ContainerConfigRequest(BaseModel):
    """컨테이너 설정 요청"""
    device: str = "cpu"  # "cpu" or "cuda"
    memory_limit: Optional[str] = None  # e.g., "4g"
    gpu_memory: Optional[str] = None  # e.g., "4g" (for GPU memory limit)


class ContainerConfigResponse(BaseModel):
    """컨테이너 설정 응답"""
    success: bool
    message: str
    service: str
    device: str
    recreated: bool


class GPUContainerStatus(BaseModel):
    """GPU 설정 컨테이너 상태 응답 (gpu_config_router 전용)"""
    service: str
    container_name: str
    running: bool
    gpu_enabled: bool
    gpu_count: int
    memory_limit: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def update_gpu_override(service_name: str, enable_gpu: bool, gpu_memory: Optional[str] = None) -> bool:
    """
    docker-compose.override.yml을 사용하여 서비스의 GPU 설정을 오버라이드합니다.
    원본 docker-compose.yml은 수정하지 않습니다.

    Args:
        service_name: Docker Compose 서비스 이름
        enable_gpu: GPU 활성화 여부
        gpu_memory: GPU 메모리 제한 (예: "4g")

    Returns:
        성공 여부
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

    Args:
        service_name: Docker Compose 서비스 이름

    Returns:
        (성공 여부, 메시지)
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
            logger.info(f"Container {container_name} stop skipped: {stop_result.stderr.strip()}")
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
            logger.info(f"Container {container_name} rm skipped: {rm_result.stderr.strip()}")
        else:
            logger.info(f"Container {container_name} removed")

        # 3. docker:24.0-cli 이미지로 재생성 (Docker Compose v2 내장)
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

        error_msg = compose_result.stderr.strip() or compose_result.stdout.strip() or 'Unknown error'
        logger.error(f"docker compose failed for {container_name}: {error_msg}")
        return False, f"Failed to recreate container: {error_msg}"

    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout while recreating {container_name}: {e}")
        return False, f"Timeout while recreating container"
    except Exception as e:
        logger.error(f"Exception while recreating {container_name}: {e}")
        return False, str(e)


# =============================================================================
# API Endpoints
# =============================================================================

@gpu_config_router.get("/container/status/{service}", response_model=GPUContainerStatus)
async def get_container_status(service: str):
    """
    컨테이너의 현재 GPU/메모리 상태를 조회합니다.

    Args:
        service: 서비스 이름 (yolo, edocr2, etc.)

    Returns:
        GPUContainerStatus with GPU and memory info
    """
    container_name = SERVICE_MAPPING.get(service, f"{service}-api")

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

        return GPUContainerStatus(
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


@gpu_config_router.post("/container/configure/{service}", response_model=ContainerConfigResponse)
async def configure_container(service: str, config: ContainerConfigRequest):
    """
    컨테이너의 GPU/메모리 설정을 변경하고 재생성합니다.

    Args:
        service: 서비스 이름 (예: yolo, edocr2 등)
        config: ContainerConfigRequest with device and memory settings

    Returns:
        ContainerConfigResponse with result
    """
    compose_service_name = SERVICE_MAPPING.get(service, f"{service}-api")
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
