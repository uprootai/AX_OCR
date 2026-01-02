"""
PID Composer API Tests
"""
import pytest
from fastapi.testclient import TestClient
import numpy as np
import base64


# Test fixtures
@pytest.fixture
def client():
    """Create test client"""
    import sys
    sys.path.insert(0, '/app')
    from api_server import app
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Create a sample test image as base64"""
    # Create a simple 100x100 white image
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    import cv2
    _, buffer = cv2.imencode('.png', img)
    return base64.b64encode(buffer).decode('utf-8')


class TestHealthEndpoints:
    """Health endpoint tests"""

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pid-composer-api"

    def test_health_check_v1(self, client):
        """Test /api/v1/health endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data


class TestInfoEndpoint:
    """Info endpoint tests"""

    def test_info(self, client):
        """Test /api/v1/info endpoint"""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "PID Composer"
        assert "supported_layers" in data
        assert "symbols" in data["supported_layers"]
        assert "lines" in data["supported_layers"]
        assert "supported_formats" in data
        assert "default_style" in data


class TestSVGEndpoint:
    """SVG generation tests"""

    def test_svg_generation(self, client):
        """Test /api/v1/compose/svg endpoint"""
        request_data = {
            "layers": {
                "symbols": [
                    {
                        "bbox": {"x": 10, "y": 10, "width": 50, "height": 40},
                        "class_name": "Valve",
                        "confidence": 0.95
                    }
                ],
                "lines": [
                    {
                        "start_point": [0, 50],
                        "end_point": [100, 50],
                        "line_type": "pipe"
                    }
                ]
            },
            "image_size": [200, 200],
            "enabled_layers": ["symbols", "lines"]
        }
        response = client.post("/api/v1/compose/svg", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "svg" in data
        assert "<svg" in data["svg"]
        assert "symbols" in data["statistics"]["enabled_layers"]

    def test_svg_empty_layers(self, client):
        """Test SVG with empty layers"""
        request_data = {
            "layers": {},
            "image_size": [100, 100],
            "enabled_layers": []
        }
        response = client.post("/api/v1/compose/svg", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestComposeEndpoint:
    """Image composition tests"""

    def test_compose_image(self, client, sample_image_base64):
        """Test /api/v1/compose endpoint"""
        request_data = {
            "image_base64": sample_image_base64,
            "layers": {
                "symbols": [
                    {
                        "bbox": {"x": 10, "y": 10, "width": 30, "height": 25},
                        "class_name": "Pump",
                        "confidence": 0.85
                    }
                ]
            },
            "enabled_layers": ["symbols"],
            "include_svg": True,
            "output_format": "png"
        }
        response = client.post("/api/v1/compose", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "image_base64" in data
        assert "svg_overlay" in data
        assert "statistics" in data

    def test_compose_with_legend(self, client, sample_image_base64):
        """Test compose with legend"""
        request_data = {
            "image_base64": sample_image_base64,
            "layers": {
                "symbols": [
                    {"bbox": {"x": 10, "y": 10, "width": 20, "height": 20}, "class_name": "Valve"}
                ],
                "lines": [
                    {"start_point": [0, 50], "end_point": [100, 50], "line_type": "pipe"}
                ]
            },
            "enabled_layers": ["symbols", "lines"],
            "include_legend": True
        }
        response = client.post("/api/v1/compose", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestLayersOnlyEndpoint:
    """Layers-only composition tests"""

    def test_layers_only(self, client):
        """Test /api/v1/compose/layers endpoint"""
        request_data = {
            "image_size": [200, 200],
            "background_color": [255, 255, 255],
            "layers": {
                "symbols": [
                    {"bbox": {"x": 50, "y": 50, "width": 100, "height": 80}, "class_name": "Tank"}
                ]
            },
            "enabled_layers": ["symbols"]
        }
        response = client.post("/api/v1/compose/layers", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "image_base64" in data


class TestPreviewEndpoint:
    """Style preview tests"""

    def test_preview_symbols(self, client):
        """Test /api/v1/preview endpoint"""
        style_data = {
            "symbol_color": [255, 100, 0],
            "symbol_thickness": 3,
            "symbol_fill_alpha": 0.2,
            "show_symbol_labels": True
        }
        response = client.post("/api/v1/preview?layer_type=symbols", json=style_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "preview_base64" in data


class TestEdgeCases:
    """Edge case tests"""

    def test_invalid_image(self, client):
        """Test with invalid base64 image"""
        request_data = {
            "image_base64": "not_valid_base64!!!",
            "layers": {},
            "enabled_layers": []
        }
        response = client.post("/api/v1/compose", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_large_layers(self, client, sample_image_base64):
        """Test with many layer items"""
        symbols = [
            {"bbox": {"x": i * 10, "y": i * 10, "width": 5, "height": 5}, "class_name": f"Symbol{i}"}
            for i in range(50)
        ]
        request_data = {
            "image_base64": sample_image_base64,
            "layers": {"symbols": symbols},
            "enabled_layers": ["symbols"]
        }
        response = client.post("/api/v1/compose", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["statistics"]["symbols_count"] == 50
