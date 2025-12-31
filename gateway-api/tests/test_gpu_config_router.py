"""
GPU Config Router Unit Tests
GPU 설정 및 컨테이너 관리 API 테스트
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestServiceMapping:
    """서비스 매핑 테스트"""

    def test_service_mapping_uses_ssot(self):
        """SERVICE_MAPPING이 constants SSOT를 사용하는지 확인"""
        from routers.gpu_config_router import SERVICE_MAPPING
        from constants import DOCKER_SERVICE_MAPPING

        # SSOT와 동일해야 함
        assert SERVICE_MAPPING == DOCKER_SERVICE_MAPPING

    def test_service_mapping_has_yolo(self):
        """yolo 서비스 매핑 확인"""
        from routers.gpu_config_router import SERVICE_MAPPING

        assert "yolo" in SERVICE_MAPPING
        assert SERVICE_MAPPING["yolo"] == "yolo-api"


class TestGPUContainerStatusModel:
    """GPUContainerStatus 모델 테스트"""

    def test_model_creation(self):
        """모델 생성 테스트"""
        from routers.gpu_config_router import GPUContainerStatus

        status = GPUContainerStatus(
            service="yolo",
            container_name="yolo-api",
            running=True,
            gpu_enabled=True,
            gpu_count=1,
            memory_limit="4g"
        )

        assert status.service == "yolo"
        assert status.running is True
        assert status.gpu_enabled is True

    def test_model_optional_memory(self):
        """memory_limit 선택적 필드"""
        from routers.gpu_config_router import GPUContainerStatus

        status = GPUContainerStatus(
            service="test",
            container_name="test-api",
            running=False,
            gpu_enabled=False,
            gpu_count=0
        )

        assert status.memory_limit is None


class TestContainerConfigRequest:
    """ContainerConfigRequest 모델 테스트"""

    def test_default_values(self):
        """기본값 확인"""
        from routers.gpu_config_router import ContainerConfigRequest

        config = ContainerConfigRequest()

        assert config.device == "cpu"
        assert config.memory_limit is None
        assert config.gpu_memory is None

    def test_cuda_config(self):
        """CUDA 설정"""
        from routers.gpu_config_router import ContainerConfigRequest

        config = ContainerConfigRequest(
            device="cuda",
            gpu_memory="4g"
        )

        assert config.device == "cuda"
        assert config.gpu_memory == "4g"


class TestContainerConfigResponse:
    """ContainerConfigResponse 모델 테스트"""

    def test_response_model(self):
        """응답 모델 생성"""
        from routers.gpu_config_router import ContainerConfigResponse

        response = ContainerConfigResponse(
            success=True,
            message="Container recreated",
            service="yolo",
            device="cuda",
            recreated=True
        )

        assert response.success is True
        assert response.recreated is True
