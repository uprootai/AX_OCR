"""
Results Router Unit Tests
파이프라인 결과 관리 API 테스트
"""

import pytest
from unittest.mock import patch, MagicMock


class TestResultsRouterEndpoints:
    """Results Router 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_result_statistics_import_error(self, client):
        """result_manager 없을 때 501 반환"""
        with patch.dict('sys.modules', {'utils.result_manager': None}):
            response = await client.get("/admin/results/stats")
            # ImportError 또는 501 반환
            assert response.status_code in [500, 501]

    @pytest.mark.asyncio
    async def test_get_recent_results_import_error(self, client):
        """result_manager 없을 때 501 반환"""
        with patch.dict('sys.modules', {'utils.result_manager': None}):
            response = await client.get("/admin/results/recent")
            assert response.status_code in [500, 501]

    @pytest.mark.asyncio
    async def test_cleanup_old_results_import_error(self, client):
        """result_manager 없을 때 501 반환"""
        with patch.dict('sys.modules', {'utils.result_manager': None}):
            response = await client.post("/admin/results/cleanup")
            assert response.status_code in [500, 501]


class TestResultsRouterLogic:
    """Results Router 로직 테스트"""

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.results_router import results_router

        assert results_router.prefix == "/admin"

    def test_router_tags(self):
        """라우터 tags 확인"""
        from routers.results_router import results_router

        assert "Results" in results_router.tags


class TestResultsRouterWithMock:
    """Results Router Mock 테스트"""

    def test_default_limit_value(self):
        """기본 limit 값 확인 (10)"""
        from routers.results_router import get_recent_results
        import inspect

        sig = inspect.signature(get_recent_results)
        limit_param = sig.parameters.get('limit')

        assert limit_param is not None
        assert limit_param.default == 10

    def test_cleanup_default_values(self):
        """cleanup 기본값 확인"""
        from routers.results_router import cleanup_old_results
        import inspect

        sig = inspect.signature(cleanup_old_results)

        max_age_param = sig.parameters.get('max_age_days')
        dry_run_param = sig.parameters.get('dry_run')

        assert max_age_param.default == 7
        assert dry_run_param.default is False
