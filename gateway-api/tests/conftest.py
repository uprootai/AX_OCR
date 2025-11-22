"""
Pytest Configuration and Fixtures
Gateway API 테스트를 위한 공통 설정 및 픽스처
"""
import sys
import pytest
from pathlib import Path
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server import app
from api_registry import APIRegistry


@pytest.fixture(scope="session")
def test_app():
    """FastAPI app fixture for testing"""
    return app


@pytest.fixture(scope="function")
def client(test_app) -> TestClient:
    """Synchronous test client"""
    return TestClient(test_app)


@pytest.fixture(scope="function")
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous test client"""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def api_registry():
    """
    API Registry fixture
    각 테스트마다 새로운 APIRegistry 인스턴스 제공
    """
    # Reset singleton for testing
    APIRegistry._instance = None
    registry = APIRegistry()
    return registry


@pytest.fixture(scope="function")
def sample_api_metadata():
    """Sample API metadata for testing"""
    return {
        "id": "test-api",
        "name": "Test API",
        "display_name": "Test API Service",
        "version": "1.0.0",
        "description": "Test API for unit testing",
        "openapi_url": "/openapi.json",
        "base_url": "http://localhost:5999",
        "endpoint": "/api/v1/test",
        "port": 5999,
        "method": "POST",
        "requires_image": True,
        "icon": "🧪",
        "color": "#00FF00",
        "category": "test",
        "inputs": [
            {
                "name": "file",
                "type": "file",
                "description": "Test file input",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "result",
                "type": "object",
                "description": "Test result output"
            }
        ],
        "parameters": [
            {
                "name": "test_param",
                "type": "string",
                "default": "test",
                "description": "Test parameter",
                "required": False
            }
        ],
        "blueprintflow": {
            "icon": "🧪",
            "color": "#00FF00",
            "category": "test"
        },
        "output_mappings": {
            "result": "data.result"
        }
    }


@pytest.fixture(autouse=True)
def cleanup_registry():
    """
    자동으로 실행되는 cleanup fixture
    각 테스트 후 APIRegistry 싱글톤 리셋
    """
    yield
    # Cleanup after test
    APIRegistry._instance = None
