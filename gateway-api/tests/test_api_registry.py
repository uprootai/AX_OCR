"""
API Registry Unit Tests
APIRegistry 클래스의 핵심 기능 테스트
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from api_registry import APIRegistry, APIMetadata, get_api_registry


@pytest.mark.unit
@pytest.mark.registry
class TestAPIMetadata:
    """APIMetadata 모델 테스트"""

    def test_api_metadata_creation(self, sample_api_metadata):
        """APIMetadata 생성 테스트"""
        api = APIMetadata(**sample_api_metadata)

        assert api.id == "test-api"
        assert api.name == "Test API"
        assert api.display_name == "Test API Service"
        assert api.version == "1.0.0"
        assert api.base_url == "http://localhost:5999"
        assert api.method == "POST"
        assert api.requires_image is True
        assert api.status == "unknown"

    def test_api_metadata_with_health_status(self, sample_api_metadata):
        """APIMetadata 헬스 상태 포함 생성 테스트"""
        sample_api_metadata["status"] = "healthy"
        sample_api_metadata["last_check"] = datetime.now()

        api = APIMetadata(**sample_api_metadata)

        assert api.status == "healthy"
        assert api.last_check is not None
        assert isinstance(api.last_check, datetime)

    def test_api_metadata_blueprintflow(self, sample_api_metadata):
        """APIMetadata BlueprintFlow 메타데이터 테스트"""
        api = APIMetadata(**sample_api_metadata)

        assert api.icon == "🧪"
        assert api.color == "#00FF00"
        assert api.category == "test"


@pytest.mark.unit
@pytest.mark.registry
class TestAPIRegistryBasics:
    """APIRegistry 기본 기능 테스트"""

    def test_registry_initialization(self, api_registry):
        """APIRegistry 초기화 테스트"""
        assert isinstance(api_registry, APIRegistry)
        assert len(api_registry.apis) == 0
        assert api_registry._health_check_interval == 60
        assert len(api_registry.default_ports) == 7

    def test_add_api(self, api_registry, sample_api_metadata):
        """API 추가 테스트"""
        api = APIMetadata(**sample_api_metadata)
        api_registry.add_api(api)

        assert len(api_registry.apis) == 1
        assert "test-api" in api_registry.apis
        assert api_registry.apis["test-api"].id == "test-api"

    def test_get_api(self, api_registry, sample_api_metadata):
        """API 조회 테스트"""
        api = APIMetadata(**sample_api_metadata)
        api_registry.add_api(api)

        retrieved = api_registry.get_api("test-api")
        assert retrieved is not None
        assert retrieved.id == "test-api"
        assert retrieved.name == "Test API"

    def test_get_nonexistent_api(self, api_registry):
        """존재하지 않는 API 조회 테스트"""
        retrieved = api_registry.get_api("nonexistent")
        assert retrieved is None

    def test_get_all_apis(self, api_registry, sample_api_metadata):
        """전체 API 목록 조회 테스트"""
        # Add multiple APIs
        for i in range(3):
            metadata = sample_api_metadata.copy()
            metadata["id"] = f"test-api-{i}"
            metadata["port"] = 5999 + i
            api = APIMetadata(**metadata)
            api_registry.add_api(api)

        all_apis = api_registry.get_all_apis()
        assert len(all_apis) == 3
        assert all(isinstance(api, APIMetadata) for api in all_apis)

    def test_remove_api(self, api_registry, sample_api_metadata):
        """API 제거 테스트"""
        api = APIMetadata(**sample_api_metadata)
        api_registry.add_api(api)

        assert len(api_registry.apis) == 1

        result = api_registry.remove_api("test-api")
        assert result is True
        assert len(api_registry.apis) == 0
        assert "test-api" not in api_registry.apis

    def test_remove_nonexistent_api(self, api_registry):
        """존재하지 않는 API 제거 테스트"""
        result = api_registry.remove_api("nonexistent")
        assert result is False


@pytest.mark.unit
@pytest.mark.registry
class TestAPIRegistryFiltering:
    """APIRegistry 필터링 기능 테스트"""

    def test_get_healthy_apis(self, api_registry, sample_api_metadata):
        """Healthy API 필터링 테스트"""
        # Add healthy API
        metadata1 = sample_api_metadata.copy()
        metadata1["id"] = "healthy-api"
        metadata1["status"] = "healthy"
        api1 = APIMetadata(**metadata1)
        api_registry.add_api(api1)

        # Add unhealthy API
        metadata2 = sample_api_metadata.copy()
        metadata2["id"] = "unhealthy-api"
        metadata2["status"] = "unhealthy"
        api2 = APIMetadata(**metadata2)
        api_registry.add_api(api2)

        # Add unknown API
        metadata3 = sample_api_metadata.copy()
        metadata3["id"] = "unknown-api"
        metadata3["status"] = "unknown"
        api3 = APIMetadata(**metadata3)
        api_registry.add_api(api3)

        healthy_apis = api_registry.get_healthy_apis()
        assert len(healthy_apis) == 1
        assert healthy_apis[0].id == "healthy-api"
        assert healthy_apis[0].status == "healthy"

    def test_get_apis_by_category(self, api_registry, sample_api_metadata):
        """카테고리별 API 필터링 테스트"""
        # Add OCR API
        metadata1 = sample_api_metadata.copy()
        metadata1["id"] = "ocr-api-1"
        metadata1["category"] = "ocr"
        api1 = APIMetadata(**metadata1)
        api_registry.add_api(api1)

        # Add another OCR API
        metadata2 = sample_api_metadata.copy()
        metadata2["id"] = "ocr-api-2"
        metadata2["category"] = "ocr"
        api2 = APIMetadata(**metadata2)
        api_registry.add_api(api2)

        # Add detection API
        metadata3 = sample_api_metadata.copy()
        metadata3["id"] = "detection-api"
        metadata3["category"] = "detection"
        api3 = APIMetadata(**metadata3)
        api_registry.add_api(api3)

        ocr_apis = api_registry.get_apis_by_category("ocr")
        assert len(ocr_apis) == 2
        assert all(api.category == "ocr" for api in ocr_apis)

        detection_apis = api_registry.get_apis_by_category("detection")
        assert len(detection_apis) == 1
        assert detection_apis[0].category == "detection"


@pytest.mark.unit
@pytest.mark.registry
class TestAPIRegistrySingleton:
    """APIRegistry 싱글톤 패턴 테스트"""

    def test_singleton_pattern(self):
        """싱글톤 인스턴스 반환 테스트"""
        # Reset singleton
        import api_registry
        api_registry._api_registry = None

        registry1 = get_api_registry()
        registry2 = get_api_registry()

        assert registry1 is registry2
        assert id(registry1) == id(registry2)

    def test_singleton_persistence(self, sample_api_metadata):
        """싱글톤 데이터 지속성 테스트"""
        # Reset singleton
        import api_registry
        api_registry._api_registry = None

        # Add API to first reference
        registry1 = get_api_registry()
        api = APIMetadata(**sample_api_metadata)
        registry1.add_api(api)

        # Get second reference and verify data persists
        registry2 = get_api_registry()
        assert len(registry2.apis) == 1
        assert "test-api" in registry2.apis


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.registry
@pytest.mark.slow
class TestAPIRegistryHealthCheck:
    """APIRegistry 헬스체크 기능 테스트"""

    async def test_check_health_success(self, api_registry, sample_api_metadata):
        """헬스체크 성공 테스트"""
        api = APIMetadata(**sample_api_metadata)
        api_registry.add_api(api)

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            status = await api_registry.check_health("test-api")

            assert status == "healthy"
            assert api_registry.apis["test-api"].status == "healthy"
            assert api_registry.apis["test-api"].last_check is not None

    async def test_check_health_failure(self, api_registry, sample_api_metadata):
        """헬스체크 실패 테스트"""
        api = APIMetadata(**sample_api_metadata)
        api_registry.add_api(api)

        # Mock httpx connection error
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            status = await api_registry.check_health("test-api")

            assert status == "unhealthy"
            assert api_registry.apis["test-api"].status == "unhealthy"

    async def test_check_health_unknown_api(self, api_registry):
        """존재하지 않는 API 헬스체크 테스트"""
        status = await api_registry.check_health("nonexistent")
        assert status == "unknown"

    async def test_check_all_health(self, api_registry, sample_api_metadata):
        """전체 API 헬스체크 테스트"""
        # Add multiple APIs
        for i in range(3):
            metadata = sample_api_metadata.copy()
            metadata["id"] = f"test-api-{i}"
            metadata["port"] = 5999 + i
            api = APIMetadata(**metadata)
            api_registry.add_api(api)

        # Mock httpx responses
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            await api_registry.check_all_health()

            # All APIs should be healthy
            for api_id in api_registry.apis:
                assert api_registry.apis[api_id].status == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.registry
@pytest.mark.slow
class TestAPIRegistryDiscovery:
    """APIRegistry 자동 검색 기능 테스트"""

    async def test_check_port_success(self, api_registry):
        """포트 체크 성공 테스트"""
        # Mock info endpoint response
        mock_info_response = MagicMock()
        mock_info_response.status_code = 200
        mock_info_response.json.return_value = {
            "id": "test-api",
            "name": "Test API",
            "display_name": "Test API Service",
            "version": "1.0.0",
            "description": "Test API",
            "endpoint": "/api/v1/test",
            "method": "POST",
            "requires_image": True,
            "inputs": [],
            "outputs": [],
            "parameters": [],
            "blueprintflow": {
                "icon": "🧪",
                "color": "#00FF00",
                "category": "test"
            },
            "output_mappings": {}
        }

        # Mock health endpoint response
        mock_health_response = MagicMock()
        mock_health_response.status_code = 200

        async def mock_get(url, **kwargs):
            if "/info" in url:
                return mock_info_response
            elif "/health" in url:
                return mock_health_response

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=mock_get)

        result = await api_registry._check_port(mock_client, "localhost", 5999)

        assert result is not None
        assert isinstance(result, APIMetadata)
        assert result.id == "test-api"
        assert result.port == 5999
        assert result.status == "healthy"

    async def test_check_port_no_service(self, api_registry):
        """서비스 없는 포트 체크 테스트"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        result = await api_registry._check_port(mock_client, "localhost", 9999)

        assert result is None

    async def test_discover_apis(self, api_registry):
        """API 자동 검색 테스트"""
        # Mock info response for port 5005 only
        mock_info_response = MagicMock()
        mock_info_response.status_code = 200
        mock_info_response.json.return_value = {
            "id": "yolo-api",
            "name": "YOLO API",
            "display_name": "YOLO Detection API",
            "version": "1.0.0",
            "description": "Object detection API",
            "endpoint": "/api/v1/detect",
            "method": "POST",
            "requires_image": True,
            "inputs": [],
            "outputs": [],
            "parameters": [],
            "blueprintflow": {
                "icon": "🎯",
                "color": "#ef4444",
                "category": "detection"
            },
            "output_mappings": {}
        }

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200

        async def mock_get(url, **kwargs):
            if "5005" in url and "/info" in url:
                return mock_info_response
            elif "5005" in url and "/health" in url:
                return mock_health_response
            else:
                raise httpx.ConnectError("Connection refused")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_get)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            discovered = await api_registry.discover_apis("localhost")

            assert len(discovered) == 1
            assert discovered[0].id == "yolo-api"
            assert discovered[0].port == 5005
            assert "yolo-api" in api_registry.apis
