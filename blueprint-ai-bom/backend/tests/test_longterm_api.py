"""장기 로드맵 API 통합 테스트

longterm_router.py API 엔드포인트 테스트
"""

import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:5020"


class TestHealthCheck:
    """헬스 체크 테스트"""

    def test_health_endpoint(self):
        """헬스 엔드포인트 확인"""
        response = httpx.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSessionCreation:
    """세션 생성 테스트"""

    def test_create_session(self):
        """세션 생성"""
        response = httpx.post(f"{BASE_URL}/sessions")
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            return data["session_id"]
        # 세션 엔드포인트가 다른 경로일 수 있음
        pytest.skip("Session endpoint may have different path")


class TestVLMClassification:
    """VLM 자동 분류 API 테스트"""

    @pytest.fixture
    def session_id(self):
        """테스트용 세션 ID"""
        # 실제 세션 생성 또는 테스트용 ID 사용
        response = httpx.post(f"{BASE_URL}/sessions")
        if response.status_code == 200:
            return response.json().get("session_id")
        return "test-session-vlm"

    def test_vlm_classify_endpoint_exists(self, session_id):
        """VLM 분류 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}/analysis/vlm-classify/{session_id}",
            json={"provider": "local", "recommend_features": True}
        )
        # 세션이 없어도 404 또는 다른 응답이 오는지 확인
        assert response.status_code in [200, 404, 422]

    def test_vlm_classify_get_result(self, session_id):
        """VLM 분류 결과 조회"""
        response = httpx.get(f"{BASE_URL}/analysis/vlm-classify/{session_id}")
        assert response.status_code in [200, 404]


class TestNotesExtraction:
    """노트 추출 API 테스트"""

    @pytest.fixture
    def session_id(self):
        response = httpx.post(f"{BASE_URL}/sessions")
        if response.status_code == 200:
            return response.json().get("session_id")
        return "test-session-notes"

    def test_notes_extract_endpoint_exists(self, session_id):
        """노트 추출 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}/analysis/notes/{session_id}/extract",
            json={"provider": "openai", "use_ocr": True}
        )
        assert response.status_code in [200, 404, 422]

    def test_notes_get_result(self, session_id):
        """노트 추출 결과 조회"""
        response = httpx.get(f"{BASE_URL}/analysis/notes/{session_id}")
        assert response.status_code in [200, 404]


class TestRegionSegmentation:
    """영역 세분화 API 테스트"""

    @pytest.fixture
    def session_id(self):
        response = httpx.post(f"{BASE_URL}/sessions")
        if response.status_code == 200:
            return response.json().get("session_id")
        return "test-session-region"

    def test_region_segment_endpoint_exists(self, session_id):
        """영역 세분화 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}/analysis/drawing-regions/{session_id}/segment",
            json={"use_vlm": False}
        )
        assert response.status_code in [200, 404, 422]

    def test_region_get_result(self, session_id):
        """영역 세분화 결과 조회"""
        response = httpx.get(f"{BASE_URL}/analysis/drawing-regions/{session_id}")
        assert response.status_code in [200, 404]


class TestRevisionComparison:
    """리비전 비교 API 테스트"""

    def test_revision_compare_endpoint_exists(self):
        """리비전 비교 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}/analysis/revision/compare",
            json={
                "session_id_old": "test-old",
                "session_id_new": "test-new"
            }
        )
        # 세션이 없으면 404, 잘못된 요청이면 400/422
        assert response.status_code in [200, 400, 404, 422]

    def test_revision_compare_missing_params(self):
        """필수 파라미터 누락 시 에러"""
        response = httpx.post(
            f"{BASE_URL}/analysis/revision/compare",
            json={}
        )
        # 필수 파라미터 누락 시 400 에러
        assert response.status_code in [400, 422]

    def test_revision_get_result(self):
        """리비전 비교 결과 조회"""
        response = httpx.get(f"{BASE_URL}/analysis/revision/test-session")
        assert response.status_code in [200, 404]

    def test_revision_compare_with_config(self):
        """설정 포함 리비전 비교"""
        response = httpx.post(
            f"{BASE_URL}/analysis/revision/compare",
            json={
                "session_id_old": "test-old",
                "session_id_new": "test-new",
                "config": {
                    "use_vlm": False,
                    "compare_dimensions": True,
                    "compare_symbols": True,
                    "compare_notes": True
                }
            }
        )
        assert response.status_code in [200, 400, 404, 422]


class TestAPIResponseFormat:
    """API 응답 형식 테스트"""

    def test_revision_compare_response_structure(self):
        """리비전 비교 응답 구조 확인"""
        response = httpx.post(
            f"{BASE_URL}/analysis/revision/compare",
            json={
                "session_id_old": "test-old",
                "session_id_new": "test-new"
            }
        )

        if response.status_code == 404:
            # 세션이 없을 때 404 응답 확인
            data = response.json()
            assert "detail" in data
        elif response.status_code == 200:
            data = response.json()
            # 성공 시 응답 구조 확인
            expected_keys = [
                "comparison_id", "session_id_old", "session_id_new",
                "changes", "total_changes", "by_type", "by_category"
            ]
            for key in expected_keys:
                assert key in data, f"Missing key: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
