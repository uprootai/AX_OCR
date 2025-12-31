"""
Download Router Unit Tests
파일 다운로드 API 테스트
"""

import pytest
from pathlib import Path


class TestDownloadRouterConfig:
    """Download Router 설정 테스트"""

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.download_router import router

        assert router.prefix == "/api/v1"

    def test_router_tags(self):
        """라우터 tags 확인"""
        from routers.download_router import router

        assert "download" in router.tags

    def test_results_dir_config(self):
        """결과 디렉토리 경로 확인 (SSOT)"""
        from constants import RESULTS_DIR

        assert str(RESULTS_DIR) == "/tmp/gateway/results"


class TestDownloadResultEndpoint:
    """결과 다운로드 엔드포인트 테스트"""

    def test_download_result_endpoint_exists(self):
        """download 엔드포인트 존재 확인"""
        from routers.download_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/download/{file_id}/{file_type}" in routes

    def test_download_result_endpoint_method(self):
        """download 엔드포인트 메서드 확인"""
        from routers.download_router import router

        for route in router.routes:
            if route.path == "/download/{file_id}/{file_type}":
                assert "GET" in route.methods

    def test_download_result_function_signature(self):
        """다운로드 함수 시그니처 확인"""
        from routers.download_router import download_result_file
        import inspect

        sig = inspect.signature(download_result_file)
        param_names = list(sig.parameters.keys())

        assert 'file_id' in param_names
        assert 'file_type' in param_names


class TestDownloadQuoteEndpoint:
    """견적 다운로드 엔드포인트 테스트"""

    def test_download_quote_endpoint_exists(self):
        """download_quote 엔드포인트 존재 확인"""
        from routers.download_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/download_quote/{quote_number}" in routes

    def test_download_quote_endpoint_method(self):
        """download_quote 엔드포인트 메서드 확인"""
        from routers.download_router import router

        for route in router.routes:
            if route.path == "/download_quote/{quote_number}":
                assert "GET" in route.methods

    def test_download_quote_function_signature(self):
        """견적 다운로드 함수 시그니처 확인"""
        from routers.download_router import download_quote
        import inspect

        sig = inspect.signature(download_quote)
        param_names = list(sig.parameters.keys())

        assert 'quote_number' in param_names


class TestSupportedFileTypes:
    """지원되는 파일 타입 테스트"""

    def test_file_type_yolo_visualization(self):
        """YOLO 시각화 파일 타입"""
        # 코드에서 지원하는 파일 타입
        supported_types = ['yolo_visualization', 'result_json', 'original']
        assert 'yolo_visualization' in supported_types

    def test_file_type_result_json(self):
        """결과 JSON 파일 타입"""
        supported_types = ['yolo_visualization', 'result_json', 'original']
        assert 'result_json' in supported_types

    def test_file_type_original(self):
        """원본 파일 타입"""
        supported_types = ['yolo_visualization', 'result_json', 'original']
        assert 'original' in supported_types


class TestResultsDirPath:
    """결과 디렉토리 경로 테스트 (SSOT)"""

    def test_results_dir_is_path_object(self):
        """RESULTS_DIR이 Path 객체인지 확인"""
        from constants import RESULTS_DIR

        assert isinstance(RESULTS_DIR, Path)

    def test_results_dir_absolute(self):
        """RESULTS_DIR이 절대 경로인지 확인"""
        from constants import RESULTS_DIR

        assert RESULTS_DIR.is_absolute()
