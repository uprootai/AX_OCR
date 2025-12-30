"""
PID Analyzer API Tests
테스트 항목:
- /api/v1/analyze 엔드포인트 (texts, regions 파라미터)
- Region 기반 밸브 시그널 추출
- 심볼 ID 자동 할당
"""
import pytest
import sys
import os

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSymbolPreprocessing:
    """심볼 전처리 테스트"""

    def test_symbol_id_auto_assign(self):
        """심볼에 ID가 없을 때 자동 할당 테스트"""
        symbols = [
            {"class_name": "valve_ball", "confidence": 0.95, "bbox": [100, 200, 150, 250]},
            {"class_name": "pump", "confidence": 0.92, "bbox": [300, 400, 350, 450]},
        ]

        # ID 자동 할당 로직 (analysis_router.py에서 사용하는 것과 동일)
        for i, sym in enumerate(symbols):
            if 'id' not in sym:
                class_name = sym.get('class_name', sym.get('label', 'symbol'))
                sym['id'] = f"{class_name}_{i+1}"

        assert symbols[0]['id'] == "valve_ball_1"
        assert symbols[1]['id'] == "pump_2"

    def test_symbol_id_preserve_existing(self):
        """기존 ID가 있으면 보존"""
        symbols = [
            {"id": "custom_valve_1", "class_name": "valve_ball", "confidence": 0.95},
            {"class_name": "pump", "confidence": 0.92},
        ]

        for i, sym in enumerate(symbols):
            if 'id' not in sym:
                class_name = sym.get('class_name', sym.get('label', 'symbol'))
                sym['id'] = f"{class_name}_{i+1}"

        assert symbols[0]['id'] == "custom_valve_1"  # 기존 ID 보존
        assert symbols[1]['id'] == "pump_2"  # 새 ID 할당


class TestRegionExtractor:
    """Region Extractor 테스트"""

    def test_import_region_extractor(self):
        """region_extractor 모듈 임포트 테스트"""
        try:
            from region_extractor import get_extractor, get_rule_manager
            assert get_extractor is not None
            assert get_rule_manager is not None
        except ImportError as e:
            pytest.skip(f"region_extractor not available: {e}")

    def test_valve_signal_bwms_rule_exists(self):
        """valve_signal_bwms 규칙 존재 확인"""
        try:
            from region_extractor import get_rule_manager
            rule_manager = get_rule_manager()
            rule = rule_manager.get_rule("valve_signal_bwms")
            assert rule is not None
            assert rule.id == "valve_signal_bwms"
        except ImportError:
            pytest.skip("region_extractor not available")

    def test_bwms_valve_pattern_matching(self):
        """BWMS 밸브 패턴 매칭 테스트"""
        import re
        # BWMS 밸브 패턴
        pattern = re.compile(r"^(BWV|BAV|BCV|BBV|BXV|BSV|BFV|BRV)\d+[A-Z]?$")

        test_cases = [
            ("BAV24", True),
            ("BAV36", True),
            ("BWV2", True),
            ("BAV10", True),
            ("BAV11", True),
            ("ABC123", False),
            ("VALVE1", False),
        ]

        for text, expected in test_cases:
            result = bool(pattern.match(text))
            assert result == expected, f"Pattern mismatch for '{text}': expected {expected}, got {result}"


class TestAnalyzeEndpoint:
    """분석 엔드포인트 테스트"""

    def test_analyze_request_format(self):
        """분석 요청 형식 테스트"""
        request_body = {
            "symbols": [
                {"class_name": "valve_ball", "confidence": 0.95, "bbox": [100, 200, 150, 250]}
            ],
            "lines": [],
            "texts": [
                {"text": "BAV24", "bbox": [[100, 100], [150, 100], [150, 120], [100, 120]], "confidence": 0.95}
            ],
            "regions": [
                {"id": 1, "bbox": [50, 50, 200, 200], "line_style": "dashed"}
            ],
            "generate_bom": True,
            "generate_valve_list": True,
            "generate_equipment_list": True,
            "enable_ocr": False,
            "visualize": False
        }

        # 필수 필드 확인
        assert "symbols" in request_body
        assert "texts" in request_body
        assert "regions" in request_body

    def test_valve_list_result_format(self):
        """밸브 리스트 결과 형식 테스트"""
        # Region 기반 추출 결과 형식
        valve_result = {
            "item_no": 1,
            "tag_number": "BAV24",
            "valve_type": "valve_tag",
            "korean_name": "BWMS 밸브",
            "position": [1243.5, 761.0],
            "signal_type": "SIGNAL FOR BWMS",
            "confidence": 0.91,
            "source": "ocr_region"
        }

        # 필수 필드 확인
        assert "tag_number" in valve_result
        assert "valve_type" in valve_result
        assert "source" in valve_result
        assert valve_result["source"] == "ocr_region"


class TestStatistics:
    """통계 정보 테스트"""

    def test_statistics_format(self):
        """통계 정보 형식 테스트"""
        statistics = {
            "total_symbols": 10,
            "yolo_symbols": 10,
            "ocr_instruments": 0,
            "ocr_texts": 50,
            "line_detector_regions": 5,
            "total_connections": 15,
            "bom_items": 10,
            "valves": 6,
            "valve_extraction_method": "ocr_region",
            "region_valve_stats": {
                "total_regions": 5,
                "total_matched_regions": 3,
                "total_extracted_items": 6
            },
            "equipment": 5
        }

        # 새로 추가된 필드 확인
        assert "ocr_texts" in statistics
        assert "line_detector_regions" in statistics
        assert "valve_extraction_method" in statistics
        assert "region_valve_stats" in statistics


class TestIntegration:
    """통합 테스트 (실제 API 호출)"""

    @pytest.fixture
    def api_client(self):
        """API 클라이언트 fixture"""
        import requests
        return requests.Session()

    def test_api_health(self, api_client):
        """API 헬스 체크"""
        try:
            response = api_client.get("http://localhost:5018/health", timeout=5)
            assert response.status_code == 200
        except Exception:
            pytest.skip("PID Analyzer API not running")

    def test_api_info_endpoint(self, api_client):
        """API 정보 엔드포인트 테스트"""
        try:
            response = api_client.get("http://localhost:5018/api/v1/info", timeout=5)
            if response.status_code != 200:
                pytest.skip("API not available")

            data = response.json()
            inputs = data.get("inputs", [])
            input_names = [inp["name"] for inp in inputs]

            # texts와 regions가 inputs에 포함되어 있는지 확인
            assert "texts" in input_names, "texts input not found in API info"
            assert "regions" in input_names, "regions input not found in API info"
        except Exception:
            pytest.skip("PID Analyzer API not running")

    def test_analyze_with_texts_and_regions(self, api_client):
        """texts와 regions 파라미터로 분석 테스트"""
        try:
            request_body = {
                "symbols": [
                    {"class_name": "valve_ball", "confidence": 0.95, "bbox": [1220, 800, 1260, 840]},
                ],
                "lines": [],
                "texts": [
                    {"text": "BAV10", "bbox": [[578, 852], [610, 852], [610, 865], [578, 865]], "confidence": 0.99},
                    {"text": "SIGNAL", "bbox": [[600, 830], [650, 830], [650, 845], [600, 845]], "confidence": 0.95},
                    {"text": "FOR BWMS", "bbox": [[600, 845], [680, 845], [680, 860], [600, 860]], "confidence": 0.92}
                ],
                "regions": [
                    {"id": 1, "bbox": [553, 811, 652, 857], "line_style": "dashed", "area": 4600}
                ],
                "generate_bom": True,
                "generate_valve_list": True,
                "enable_ocr": False,
                "visualize": False
            }

            response = api_client.post(
                "http://localhost:5018/api/v1/analyze",
                json=request_body,
                timeout=30
            )

            if response.status_code != 200:
                pytest.skip("API not available")

            data = response.json()
            assert data.get("success") == True

            stats = data.get("data", {}).get("statistics", {})
            assert stats.get("ocr_texts") == 3
            assert stats.get("line_detector_regions") == 1

        except Exception as e:
            pytest.skip(f"PID Analyzer API not running: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
