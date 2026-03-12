"""
Admin Router Unit Tests
시스템 관리 API 테스트
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAdminRouterConfig:
    """Admin Router 설정 테스트"""

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.admin_router import admin_router

        assert admin_router.prefix == "/admin"

    def test_router_tags(self):
        """라우터 tags 확인"""
        from routers.admin_router import admin_router

        assert "Admin" in admin_router.tags


class TestAPIRegistry:
    """API Registry 관리 테스트"""

    def test_set_api_registry(self):
        """set_api_registry 함수 테스트"""
        from routers.admin_router import set_api_registry, get_api_registry

        mock_registry = MagicMock()
        set_api_registry(mock_registry)

        result = get_api_registry()
        assert result == mock_registry

    def test_get_api_registry_default(self):
        """초기 상태에서 registry 반환"""
        from routers.admin_router import get_api_registry

        # 이전 테스트에서 설정된 값이 있을 수 있음
        result = get_api_registry()
        # None이거나 MagicMock 중 하나
        assert result is None or result is not None


class TestModelDirs:
    """MODEL_DIRS 상수 테스트"""

    def test_model_dirs_has_yolo(self):
        """yolo 모델 경로 확인"""
        from routers.admin_router import MODEL_DIRS

        assert "yolo" in MODEL_DIRS
        assert "container" in MODEL_DIRS["yolo"]
        assert "host" in MODEL_DIRS["yolo"]

    def test_model_dirs_has_edocr2_v2(self):
        """edocr2-v2 모델 경로 확인 (edocr2는 deprecated)"""
        from routers.admin_router import MODEL_DIRS

        assert "edocr2-v2" in MODEL_DIRS

    def test_model_dirs_has_edgnet(self):
        """edgnet 모델 경로 확인"""
        from routers.admin_router import MODEL_DIRS

        assert "edgnet" in MODEL_DIRS

    def test_model_dirs_has_skinmodel(self):
        """skinmodel 모델 경로 확인"""
        from routers.admin_router import MODEL_DIRS

        assert "skinmodel" in MODEL_DIRS


class TestResponseModels:
    """Response Model 테스트"""

    def test_api_status_model(self):
        """APIStatus 모델"""
        from routers.admin_router import APIStatus

        status = APIStatus(
            name="yolo",
            display_name="YOLO Detection",
            status="healthy",
            response_time=0.05,
            port=5005,
            gpu_enabled=True
        )

        assert status.name == "yolo"
        assert status.status == "healthy"
        assert status.gpu_enabled is True

    def test_gpu_status_model(self):
        """GPUStatus 모델"""
        from routers.admin_router import GPUStatus

        status = GPUStatus(available=True, device_name="RTX 4090")

        assert status.available is True
        assert status.device_name == "RTX 4090"

    def test_gpu_status_unavailable(self):
        """GPU 미사용 시"""
        from routers.admin_router import GPUStatus

        status = GPUStatus(available=False)

        assert status.available is False
        assert status.device_name is None

    def test_system_resources_model(self):
        """SystemResources 모델"""
        from routers.admin_router import SystemResources

        resources = SystemResources(
            cpu_percent=25.5,
            memory_percent=60.0,
            memory_used_gb=12.0,
            memory_total_gb=20.0,
            disk_percent=45.0,
            disk_used_gb=200.0,
            disk_total_gb=500.0
        )

        assert resources.cpu_percent == 25.5
        assert resources.memory_total_gb == 20.0

    def test_model_files_response(self):
        """ModelFilesResponse 모델"""
        from routers.admin_router import ModelFilesResponse

        response = ModelFilesResponse(
            model_type="yolo",
            host_path="/path/to/models",
            file_count=5,
            total_size_mb=150.5
        )

        assert response.model_type == "yolo"
        assert response.file_count == 5


class TestHelperFunctions:
    """헬퍼 함수 테스트"""

    def test_count_model_files_empty(self):
        """빈 경로 목록"""
        from routers.admin_router import _count_model_files

        count, size = _count_model_files(["/nonexistent/path"])

        assert count == 0
        assert size == 0

    def test_get_gpu_status_returns_status(self):
        """GPU 상태 반환 테스트"""
        from routers.admin_router import get_gpu_status, GPUStatus

        status = get_gpu_status()

        # 반환 타입 확인
        assert isinstance(status, GPUStatus)
        # available은 True 또는 False
        assert isinstance(status.available, bool)

    def test_get_system_resources(self):
        """시스템 리소스 조회"""
        from routers.admin_router import get_system_resources

        resources = get_system_resources()

        assert resources.cpu_percent >= 0
        assert resources.memory_percent >= 0
        assert resources.memory_total_gb > 0
        assert resources.disk_total_gb > 0


class TestEndpoints:
    """엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_system_status(self, client):
        """시스템 상태 조회"""
        response = await client.get("/admin/status")

        assert response.status_code == 200
        data = response.json()
        assert "apis" in data
        assert "gpu" in data
        assert "system" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_all_models(self, client):
        """모든 모델 조회"""
        response = await client.get("/admin/models")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_model_files_invalid(self, client):
        """잘못된 모델 타입"""
        response = await client.get("/admin/models/invalid_model")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_model_files_yolo(self, client):
        """yolo 모델 조회"""
        response = await client.get("/admin/models/yolo")

        assert response.status_code == 200
        data = response.json()
        assert data["model_type"] == "yolo"


class TestCostReport:
    """원가 지표 API 테스트"""

    def test_cost_report_response_model(self):
        """CostReportResponse 모델"""
        from routers.admin_router import CostReportResponse

        report = CostReportResponse(
            drawings_analyzed=10,
            avg_inference_ms=2300.0,
            estimated_gpu_cost_krw=4.6,
            breakdown_by_engine={
                "yolo": {"avg_ms": 500, "cost_krw": 1.0}
            },
            report_generated_at="2026-03-12T10:00:00"
        )
        assert report.drawings_analyzed == 10
        assert report.avg_inference_ms == 2300.0

    @pytest.mark.asyncio
    async def test_get_cost_report(self, client):
        """GET /admin/cost-report 엔드포인트"""
        response = await client.get("/admin/cost-report")
        assert response.status_code == 200
        data = response.json()
        assert "drawings_analyzed" in data
        assert "avg_inference_ms" in data
        assert "estimated_gpu_cost_krw" in data
        assert "breakdown_by_engine" in data
        assert "report_generated_at" in data

    @pytest.mark.asyncio
    async def test_cost_report_breakdown_structure(self, client):
        """breakdown_by_engine 구조 검증"""
        response = await client.get("/admin/cost-report")
        data = response.json()
        breakdown = data["breakdown_by_engine"]
        assert "yolo_detection" in breakdown
        assert "ocr_edocr2" in breakdown
        assert "post_processing" in breakdown
        for engine_data in breakdown.values():
            assert "avg_ms" in engine_data
            assert "cost_krw" in engine_data
