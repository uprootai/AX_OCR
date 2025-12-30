"""
Registry Endpoints Integration Tests
Gateway API의 Registry 엔드포인트 통합 테스트

2025-12-30: httpx 0.28+ 호환성을 위해 모든 테스트를 async로 변환
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api_registry import APIRegistry, APIMetadata, get_api_registry


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
class TestRegistryListEndpoint:
    """GET /api/v1/registry/list 엔드포인트 테스트"""

    async def test_get_registry_list_empty(self, client):
        """빈 레지스트리 조회 테스트"""
        # Reset registry
        import api_registry
        api_registry._api_registry = None

        response = await client.get("/api/v1/registry/list")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_count"] == 0
        assert data["apis"] == []

    async def test_get_registry_list_with_apis(self, client, sample_api_metadata):
        """API가 등록된 레지스트리 조회 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        # Add multiple APIs
        for i in range(3):
            metadata = sample_api_metadata.copy()
            metadata["id"] = f"test-api-{i}"
            metadata["port"] = 5999 + i
            api = APIMetadata(**metadata)
            registry.add_api(api)

        response = await client.get("/api/v1/registry/list")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_count"] == 3
        assert len(data["apis"]) == 3
        assert all("id" in api for api in data["apis"])


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
class TestRegistryHealthyEndpoint:
    """GET /api/v1/registry/healthy 엔드포인트 테스트"""

    async def test_get_healthy_apis_empty(self, client):
        """Healthy API 없을 때 조회 테스트"""
        # Reset registry
        import api_registry
        api_registry._api_registry = None

        response = await client.get("/api/v1/registry/healthy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 0
        assert data["apis"] == []

    async def test_get_healthy_apis_filtered(self, client, sample_api_metadata):
        """Healthy API만 필터링 조회 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        # Add healthy API
        metadata1 = sample_api_metadata.copy()
        metadata1["id"] = "healthy-api-1"
        metadata1["status"] = "healthy"
        api1 = APIMetadata(**metadata1)
        registry.add_api(api1)

        # Add another healthy API
        metadata2 = sample_api_metadata.copy()
        metadata2["id"] = "healthy-api-2"
        metadata2["status"] = "healthy"
        metadata2["port"] = 6000
        api2 = APIMetadata(**metadata2)
        registry.add_api(api2)

        # Add unhealthy API
        metadata3 = sample_api_metadata.copy()
        metadata3["id"] = "unhealthy-api"
        metadata3["status"] = "unhealthy"
        metadata3["port"] = 6001
        api3 = APIMetadata(**metadata3)
        registry.add_api(api3)

        response = await client.get("/api/v1/registry/healthy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["apis"]) == 2
        assert all(api["status"] == "healthy" for api in data["apis"])


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
class TestRegistryGetAPIEndpoint:
    """GET /api/v1/registry/{api_id} 엔드포인트 테스트"""

    async def test_get_api_by_id_success(self, client, sample_api_metadata):
        """API ID로 조회 성공 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        api = APIMetadata(**sample_api_metadata)
        registry.add_api(api)

        response = await client.get("/api/v1/registry/test-api")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["api"]["id"] == "test-api"
        assert data["api"]["name"] == "Test API"

    async def test_get_api_by_id_not_found(self, client):
        """존재하지 않는 API 조회 테스트"""
        # Reset registry
        import api_registry
        api_registry._api_registry = None

        response = await client.get("/api/v1/registry/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
class TestRegistryCategoryEndpoint:
    """GET /api/v1/registry/category/{category} 엔드포인트 테스트"""

    async def test_get_apis_by_category_success(self, client, sample_api_metadata):
        """카테고리별 API 조회 성공 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        # Add OCR APIs
        for i in range(2):
            metadata = sample_api_metadata.copy()
            metadata["id"] = f"ocr-api-{i}"
            metadata["category"] = "ocr"
            metadata["port"] = 5999 + i
            api = APIMetadata(**metadata)
            registry.add_api(api)

        # Add detection API
        metadata_detection = sample_api_metadata.copy()
        metadata_detection["id"] = "detection-api"
        metadata_detection["category"] = "detection"
        metadata_detection["port"] = 6001
        api_detection = APIMetadata(**metadata_detection)
        registry.add_api(api_detection)

        response = await client.get("/api/v1/registry/category/ocr")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert data["category"] == "ocr"
        assert all(api["category"] == "ocr" for api in data["apis"])

    async def test_get_apis_by_category_empty(self, client):
        """존재하지 않는 카테고리 조회 테스트"""
        # Reset registry
        import api_registry
        api_registry._api_registry = None

        response = await client.get("/api/v1/registry/category/nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 0
        assert data["apis"] == []


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
@pytest.mark.slow
class TestRegistryDiscoverEndpoint:
    """GET /api/v1/registry/discover 엔드포인트 테스트"""

    async def test_discover_apis_endpoint(self, async_client, sample_api_metadata):
        """API 자동 검색 엔드포인트 테스트"""
        # Reset registry
        import api_registry
        api_registry._api_registry = None

        # Mock discover_apis to return sample API
        with patch.object(APIRegistry, "discover_apis") as mock_discover:
            mock_api = APIMetadata(**sample_api_metadata)
            mock_discover.return_value = [mock_api]

            response = await async_client.get("/api/v1/registry/discover")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["discovered_count"] >= 0
            assert "apis" in data
            mock_discover.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
@pytest.mark.slow
class TestRegistryHealthCheckEndpoint:
    """POST /api/v1/registry/health-check 엔드포인트 테스트"""

    async def test_manual_health_check(self, async_client, sample_api_metadata):
        """수동 헬스체크 엔드포인트 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        api = APIMetadata(**sample_api_metadata)
        registry.add_api(api)

        # Mock check_all_health
        with patch.object(APIRegistry, "check_all_health", new_callable=AsyncMock) as mock_check:
            response = await async_client.post("/api/v1/registry/health-check")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "total_apis" in data
            assert "healthy_apis" in data
            mock_check.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.endpoints
class TestRegistryEdgeCases:
    """Registry 엔드포인트 엣지 케이스 테스트"""

    async def test_registry_endpoint_route_ordering(self, client, sample_api_metadata):
        """
        라우트 순서 테스트
        /registry/healthy가 /registry/{api_id}보다 먼저 매칭되는지 확인
        """
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        # Add API with id "healthy" (edge case)
        metadata = sample_api_metadata.copy()
        metadata["id"] = "healthy"
        api = APIMetadata(**metadata)
        registry.add_api(api)

        # Should return healthy APIs, not the API with id "healthy"
        response = await client.get("/api/v1/registry/healthy")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Should have "count" and "apis" keys (not "api" key from get_api endpoint)
        assert "count" in data
        assert "apis" in data
        assert "api" not in data  # This would indicate wrong endpoint matched

    async def test_multiple_concurrent_requests(self, client, sample_api_metadata):
        """동시 요청 처리 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        for i in range(5):
            metadata = sample_api_metadata.copy()
            metadata["id"] = f"test-api-{i}"
            metadata["port"] = 5999 + i
            api = APIMetadata(**metadata)
            registry.add_api(api)

        # Make multiple concurrent requests
        responses = []
        for _ in range(10):
            response = await client.get("/api/v1/registry/list")
            responses.append(response)

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["total_count"] == 5 for r in responses)

    async def test_registry_persistence_across_requests(self, client, sample_api_metadata):
        """요청 간 레지스트리 데이터 지속성 테스트"""
        # Reset and populate registry
        import api_registry
        api_registry._api_registry = None
        registry = get_api_registry()

        api = APIMetadata(**sample_api_metadata)
        registry.add_api(api)

        # First request
        response1 = await client.get("/api/v1/registry/list")
        assert response1.status_code == 200
        assert response1.json()["total_count"] == 1

        # Second request should see same data
        response2 = await client.get("/api/v1/registry/list")
        assert response2.status_code == 200
        assert response2.json()["total_count"] == 1
        assert response2.json()["apis"][0]["id"] == "test-api"
