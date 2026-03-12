"""
Table Detector Service Unit Tests
GPU 불필요 — mock 기반 단위 테스트
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHealthEndpoint:
    """헬스체크 엔드포인트 테스트"""

    def test_app_creation(self):
        """FastAPI 앱 생성 확인"""
        from api_server import app
        assert app.title == "Table Detector API"

    def test_health_response_model(self):
        """HealthResponse 모델 구조"""
        from api_server import HealthResponse
        resp = HealthResponse(
            status="healthy",
            service="table-detector-api",
            version="1.0.0",
            timestamp="2026-03-12T00:00:00",
            models_loaded=True
        )
        assert resp.status == "healthy"
        assert resp.models_loaded is True


class TestTableDetectorService:
    """테이블 검출 서비스 로직 테스트"""

    def test_detect_tables_fallback_without_model(self):
        """TATR 모델 없이 fallback 동작"""
        from services.table_detector_service import detect_tables

        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='white')

        # With no model loaded, should return full image as fallback
        with patch('services.table_detector_service._tatr_model', None), \
             patch('services.table_detector_service._tatr_processor', None):
            results = detect_tables(img, confidence_threshold=0.7)

        assert len(results) >= 1
        assert results[0]["bbox"] == [0, 0, 800, 600]
        assert results[0]["label"] == "table"

    def test_extract_table_content_unavailable(self):
        """img2table 미설치 시 에러 응답"""
        from services.table_detector_service import extract_table_content

        img = Image.new('RGB', (400, 300), color='white')

        with patch('services.table_detector_service._img2table_available', False):
            results = extract_table_content(img)

        assert len(results) == 1
        assert "error" in results[0]

    def test_analyze_tables_integration(self):
        """analyze_tables 통합 함수 테스트"""
        from services.table_detector_service import analyze_tables

        img = Image.new('RGB', (800, 600), color='white')

        with patch('services.table_detector_service._tatr_model', None), \
             patch('services.table_detector_service._tatr_processor', None), \
             patch('services.table_detector_service._img2table_available', False):
            result = analyze_tables(img)

        assert "image_size" in result
        assert result["image_size"]["width"] == 800
        assert result["image_size"]["height"] == 600
        assert "regions_detected" in result
        assert "tables_extracted" in result


class TestRouterSchemas:
    """라우터 스키마 테스트"""

    def test_detect_response_model(self):
        """DetectResponse 모델"""
        from routers.table_router import DetectResponse, TableRegion

        resp = DetectResponse(
            success=True,
            image_size={"width": 800, "height": 600},
            regions=[TableRegion(id=0, bbox=[0, 0, 800, 600], confidence=0.95, label="table")],
            processing_time_ms=150.5,
            timestamp="2026-03-12T00:00:00"
        )
        assert resp.success is True
        assert len(resp.regions) == 1

    def test_extract_response_model(self):
        """ExtractResponse 모델"""
        from routers.table_router import ExtractResponse

        resp = ExtractResponse(
            success=True,
            tables_count=2,
            tables=[{"id": 0, "rows": 5, "cols": 3}],
            processing_time_ms=500.0,
            timestamp="2026-03-12T00:00:00"
        )
        assert resp.tables_count == 2

    def test_info_endpoint_exists(self):
        """GET /info 라우터 등록 확인"""
        from routers.table_router import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/info" in routes or "/info" in [r.path for r in router.routes]
