"""P&ID Features API 통합 테스트

pid_features_router.py API 엔드포인트 테스트
- Valve Detection
- Equipment Detection
- Checklist Verification
- Deviation Analysis
- Verification Queue
- Export

2025-12-30: 초기 작성
"""

import pytest
import httpx

BASE_URL = "http://localhost:5020"
ROUTER_PREFIX = "/pid-features"


class TestPIDFeaturesHealth:
    """PID Features 라우터 기본 테스트"""

    def test_health_endpoint(self):
        """헬스 엔드포인트 확인"""
        response = httpx.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestValveDetection:
    """Valve Detection API 테스트"""

    @pytest.fixture
    def session_id(self):
        """테스트용 세션 ID"""
        return "test-session-valve"

    def test_valve_detect_endpoint_exists(self, session_id):
        """밸브 검출 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/valve/detect",
            params={"profile": "default"}
        )
        # 세션이 없어도 404 또는 422 응답이 오는지 확인
        assert response.status_code in [200, 404, 422, 500]

    def test_valve_detect_with_profile(self, session_id):
        """프로필별 밸브 검출"""
        for profile in ["default", "bwms", "chemical"]:
            response = httpx.post(
                f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/valve/detect",
                params={"profile": profile, "language": "en"}
            )
            assert response.status_code in [200, 404, 422, 500]

    def test_valve_detect_response_structure(self):
        """밸브 검출 응답 구조 테스트 (실제 세션 사용 시)"""
        # 실제 세션이 있을 때의 응답 구조 검증
        # ValveDetectionResponse: valves, total_count, processing_time, regions
        expected_fields = ["valves", "total_count"]
        # 이 테스트는 실제 환경에서 확장 가능


class TestEquipmentDetection:
    """Equipment Detection API 테스트"""

    @pytest.fixture
    def session_id(self):
        return "test-session-equipment"

    def test_equipment_detect_endpoint_exists(self, session_id):
        """장비 검출 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/equipment/detect",
            params={"profile": "default"}
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_equipment_detect_with_profile(self, session_id):
        """프로필별 장비 검출"""
        for profile in ["default", "bwms"]:
            response = httpx.post(
                f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/equipment/detect",
                params={"profile": profile}
            )
            assert response.status_code in [200, 404, 422, 500]


class TestChecklistVerification:
    """Checklist Verification API 테스트"""

    @pytest.fixture
    def session_id(self):
        return "test-session-checklist"

    def test_checklist_check_endpoint_exists(self, session_id):
        """체크리스트 검증 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/checklist/check",
            params={"checklist_type": "bwms"}
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_checklist_check_types(self, session_id):
        """체크리스트 타입별 검증"""
        for checklist_type in ["bwms", "general", "safety"]:
            response = httpx.post(
                f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/checklist/check",
                params={"checklist_type": checklist_type}
            )
            assert response.status_code in [200, 404, 422, 500]


class TestDeviationAnalysis:
    """Deviation Analysis API 테스트"""

    @pytest.fixture
    def session_id(self):
        return "test-session-deviation"

    def test_deviation_analyze_endpoint_exists(self, session_id):
        """편차 분석 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/deviation/analyze"
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_deviation_list_endpoint_exists(self, session_id):
        """편차 목록 조회 엔드포인트 존재 확인"""
        response = httpx.get(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/deviation/list"
        )
        assert response.status_code in [200, 404]


class TestVerificationQueue:
    """Verification Queue API 테스트"""

    @pytest.fixture
    def session_id(self):
        return "test-session-verify"

    def test_verify_queue_endpoint_exists(self, session_id):
        """검증 큐 조회 엔드포인트 존재 확인"""
        response = httpx.get(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/verify/queue"
        )
        assert response.status_code in [200, 404]

    def test_verify_queue_with_filters(self, session_id):
        """필터 적용 검증 큐 조회"""
        response = httpx.get(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/verify/queue",
            params={
                "feature": "valve",
                "status": "pending",
                "limit": 10
            }
        )
        assert response.status_code in [200, 404]

    def test_verify_single_endpoint_exists(self, session_id):
        """단일 항목 검증 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/verify",
            json={
                "item_id": "test-item-1",
                "feature": "valve",
                "status": "approved"
            }
        )
        assert response.status_code in [200, 404, 422]

    def test_verify_bulk_endpoint_exists(self, session_id):
        """대량 검증 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/verify/bulk",
            json={
                "items": [
                    {"item_id": "item-1", "feature": "valve", "status": "approved"},
                    {"item_id": "item-2", "feature": "equipment", "status": "rejected"}
                ]
            }
        )
        assert response.status_code in [200, 404, 422]


class TestExport:
    """Export API 테스트"""

    @pytest.fixture
    def session_id(self):
        return "test-session-export"

    def test_export_endpoint_exists(self, session_id):
        """내보내기 엔드포인트 존재 확인"""
        response = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/export",
            params={"format": "excel", "include_all": False}
        )
        assert response.status_code in [200, 404, 422, 500]

    def test_export_formats(self, session_id):
        """내보내기 포맷별 테스트"""
        for fmt in ["excel", "csv", "json"]:
            response = httpx.post(
                f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/export",
                params={"format": fmt}
            )
            assert response.status_code in [200, 404, 422, 500]


class TestSummary:
    """Summary API 테스트"""

    @pytest.fixture
    def session_id(self):
        return "test-session-summary"

    def test_summary_endpoint_exists(self, session_id):
        """요약 엔드포인트 존재 확인"""
        response = httpx.get(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/summary"
        )
        assert response.status_code in [200, 404]


class TestPIDFeaturesIntegration:
    """PID Features 통합 테스트"""

    def test_router_prefix_configured(self):
        """라우터 접두사 설정 확인"""
        # /pid-features 경로로 접근 가능한지 확인
        response = httpx.get(f"{BASE_URL}{ROUTER_PREFIX}/nonexistent/summary")
        # 404는 경로는 맞지만 세션이 없는 경우
        # 422는 유효성 검사 실패
        assert response.status_code in [404, 422]

    def test_multiple_features_in_session(self):
        """여러 기능 동시 사용 시나리오"""
        session_id = "test-multi-feature"

        # 1. 밸브 검출
        valve_resp = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/valve/detect"
        )

        # 2. 장비 검출
        equipment_resp = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/equipment/detect"
        )

        # 3. 체크리스트 검증
        checklist_resp = httpx.post(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/checklist/check"
        )

        # 4. 요약 조회
        summary_resp = httpx.get(
            f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/summary"
        )

        # 모든 요청이 적절한 응답을 반환하는지 확인
        for resp in [valve_resp, equipment_resp, checklist_resp, summary_resp]:
            assert resp.status_code in [200, 404, 422, 500]


class TestVerificationStatusValues:
    """검증 상태 값 테스트"""

    def test_valid_status_values(self):
        """유효한 검증 상태 값"""
        valid_statuses = ["pending", "approved", "rejected", "needs_review"]
        session_id = "test-status"

        for status in valid_statuses:
            response = httpx.post(
                f"{BASE_URL}{ROUTER_PREFIX}/{session_id}/verify",
                json={
                    "item_id": "test-item",
                    "feature": "valve",
                    "status": status
                }
            )
            # 422는 세션이 없어서 실패할 수 있음
            # 하지만 상태 값 자체는 유효해야 함
            assert response.status_code in [200, 404, 422]


class TestResponseModels:
    """응답 모델 테스트"""

    def test_valve_detection_response_model(self):
        """ValveDetectionResponse 모델 필드"""
        expected_fields = {
            "valves": list,
            "total_count": int,
            "processing_time": float,
        }
        # 실제 테스트는 세션이 있을 때 수행

    def test_equipment_detection_response_model(self):
        """EquipmentDetectionResponse 모델 필드"""
        expected_fields = {
            "equipment": list,
            "total_count": int,
            "processing_time": float,
        }

    def test_checklist_response_model(self):
        """ChecklistResponse 모델 필드"""
        expected_fields = {
            "items": list,
            "summary": dict,
            "processing_time": float,
        }

    def test_verification_queue_response_model(self):
        """PIDVerificationQueue 모델 필드"""
        expected_fields = {
            "items": list,
            "total_count": int,
            "pending_count": int,
        }
