"""
Process Router Unit Tests
파이프라인 처리 API 테스트
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestProcessRouterConfig:
    """Process Router 설정 테스트"""

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.process_router import router

        assert router.prefix == "/api/v1"

    def test_router_tags(self):
        """라우터 tags 확인"""
        from routers.process_router import router

        assert "process" in router.tags

    def test_results_dir_exists(self):
        """결과 디렉토리 경로 확인 (SSOT)"""
        from constants import RESULTS_DIR

        assert str(RESULTS_DIR) == "/tmp/gateway/results"


class TestProgressEndpoint:
    """진행률 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_progress_stream(self, client):
        """SSE 엔드포인트 접근 테스트"""
        response = await client.get("/api/v1/progress/test-job-id")

        # SSE 엔드포인트는 스트리밍 응답 반환
        assert response.status_code == 200


class TestProcessEndpoint:
    """처리 엔드포인트 테스트"""

    def test_process_endpoint_exists(self):
        """process 엔드포인트 존재 확인"""
        from routers.process_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/process" in routes

    def test_process_endpoint_method(self):
        """process 엔드포인트 메서드 확인"""
        from routers.process_router import router

        for route in router.routes:
            if route.path == "/api/v1/process":
                assert "POST" in route.methods


class TestProgressStore:
    """진행률 저장소 테스트"""

    def test_progress_store_import(self):
        """progress_store import 확인"""
        from utils import progress_store

        assert progress_store is not None
        assert isinstance(progress_store, dict)

    def test_progress_tracker_class(self):
        """ProgressTracker 클래스 존재 확인"""
        from utils import ProgressTracker

        assert ProgressTracker is not None


class TestProcessFormParameters:
    """처리 폼 파라미터 테스트"""

    def test_default_pipeline_mode(self):
        """기본 파이프라인 모드"""
        from routers.process_router import process_drawing
        import inspect

        sig = inspect.signature(process_drawing)
        pipeline_mode_param = sig.parameters.get('pipeline_mode')

        assert pipeline_mode_param is not None

    def test_form_parameters_exist(self):
        """폼 파라미터 존재 확인"""
        from routers.process_router import process_drawing
        import inspect

        sig = inspect.signature(process_drawing)
        param_names = list(sig.parameters.keys())

        expected_params = [
            'file', 'pipeline_mode', 'use_segmentation',
            'use_ocr', 'use_tolerance', 'visualize'
        ]

        for param in expected_params:
            assert param in param_names, f"Missing parameter: {param}"


class TestServiceImports:
    """서비스 함수 import 테스트"""

    def test_yolo_service_import(self):
        """YOLO 서비스 import"""
        from services import call_yolo_detect

        assert call_yolo_detect is not None

    def test_ocr_service_import(self):
        """OCR 서비스 import"""
        from services import call_edocr2_ocr

        assert call_edocr2_ocr is not None

    def test_segmentation_service_import(self):
        """세그멘테이션 서비스 import"""
        from services import call_edgnet_segment

        assert call_edgnet_segment is not None

    def test_tolerance_service_import(self):
        """공차 서비스 import"""
        from services import call_skinmodel_tolerance

        assert call_skinmodel_tolerance is not None


class TestUtilsImports:
    """유틸리티 함수 import 테스트"""

    def test_pdf_to_image_import(self):
        """PDF 변환 함수 import"""
        from utils import pdf_to_image

        assert pdf_to_image is not None

    def test_crop_bbox_import(self):
        """bbox 크롭 함수 import"""
        from utils import crop_bbox

        assert crop_bbox is not None

    def test_visualization_imports(self):
        """시각화 함수 imports"""
        from utils import (
            create_ocr_visualization,
            create_edgnet_visualization,
            create_ensemble_visualization,
            redraw_yolo_visualization
        )

        assert create_ocr_visualization is not None
        assert create_edgnet_visualization is not None
        assert create_ensemble_visualization is not None
        assert redraw_yolo_visualization is not None
