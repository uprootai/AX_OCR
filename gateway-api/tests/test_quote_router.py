"""
Quote Router Unit Tests
견적 생성 API 테스트
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestQuoteRouterConfig:
    """Quote Router 설정 테스트"""

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.quote_router import router

        assert router.prefix == "/api/v1"

    def test_router_tags(self):
        """라우터 tags 확인"""
        from routers.quote_router import router

        assert "quote" in router.tags

    def test_vl_api_url_config(self):
        """VL API URL 설정 확인"""
        from routers.quote_router import VL_API_URL

        assert "vl-api" in VL_API_URL or "5004" in VL_API_URL

    def test_results_dir_config(self):
        """결과 디렉토리 경로 확인 (SSOT)"""
        from constants import RESULTS_DIR

        assert str(RESULTS_DIR) == "/tmp/gateway/results"


class TestQuoteEndpoint:
    """견적 엔드포인트 테스트"""

    def test_quote_endpoint_exists(self):
        """quote 엔드포인트 존재 확인"""
        from routers.quote_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/quote" in routes

    def test_quote_endpoint_method(self):
        """quote 엔드포인트 메서드 확인"""
        from routers.quote_router import router

        for route in router.routes:
            if route.path == "/quote":
                assert "POST" in route.methods

    def test_quote_form_parameters(self):
        """견적 폼 파라미터 확인"""
        from routers.quote_router import generate_quote
        import inspect

        sig = inspect.signature(generate_quote)
        param_names = list(sig.parameters.keys())

        expected_params = [
            'file', 'material_cost_per_kg', 'machining_rate_per_hour',
            'tolerance_premium_factor', 'skin_material',
            'skin_manufacturing_process', 'skin_correlation_length'
        ]

        for param in expected_params:
            assert param in param_names, f"Missing parameter: {param}"


class TestProcessWithVLEndpoint:
    """VL 처리 엔드포인트 테스트"""

    def test_process_with_vl_endpoint_exists(self):
        """process_with_vl 엔드포인트 존재 확인"""
        from routers.quote_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/process_with_vl" in routes

    def test_process_with_vl_endpoint_method(self):
        """process_with_vl 엔드포인트 메서드 확인"""
        from routers.quote_router import router

        for route in router.routes:
            if route.path == "/process_with_vl":
                assert "POST" in route.methods

    def test_process_with_vl_form_parameters(self):
        """VL 처리 폼 파라미터 확인"""
        from routers.quote_router import process_with_vl
        import inspect

        sig = inspect.signature(process_with_vl)
        param_names = list(sig.parameters.keys())

        expected_params = ['file', 'model', 'quantity', 'customer_name']

        for param in expected_params:
            assert param in param_names, f"Missing parameter: {param}"


class TestServiceImports:
    """서비스 함수 import 테스트"""

    def test_edocr2_service_import(self):
        """eDOCr2 서비스 import"""
        from services import call_edocr2_ocr

        assert call_edocr2_ocr is not None

    def test_edgnet_service_import(self):
        """EDGNet 서비스 import"""
        from services import call_edgnet_segment

        assert call_edgnet_segment is not None

    def test_skinmodel_service_import(self):
        """SkinModel 서비스 import"""
        from services import call_skinmodel_tolerance

        assert call_skinmodel_tolerance is not None

    def test_calculate_quote_import(self):
        """견적 계산 함수 import"""
        from services import calculate_quote

        assert calculate_quote is not None


class TestUtilityImports:
    """유틸리티 함수 import 테스트"""

    def test_pdf_to_image_import(self):
        """PDF 변환 함수 import"""
        from utils import pdf_to_image

        assert pdf_to_image is not None

    def test_cost_estimator_import(self):
        """비용 추정기 import"""
        from cost_estimator import get_cost_estimator

        assert get_cost_estimator is not None

    def test_pdf_generator_import(self):
        """PDF 생성기 import"""
        from pdf_generator import get_pdf_generator

        assert get_pdf_generator is not None


class TestQuoteResponseModel:
    """견적 응답 모델 테스트"""

    def test_quote_response_model_exists(self):
        """QuoteResponse 모델 존재 확인"""
        from models import QuoteResponse

        assert QuoteResponse is not None

    def test_quote_response_fields(self):
        """QuoteResponse 필드 확인"""
        from models import QuoteResponse

        # Pydantic 모델 필드 확인
        fields = QuoteResponse.model_fields.keys()
        assert 'status' in fields
        assert 'data' in fields
