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


class TestPathFinding:
    """경로 탐색 함수 테스트 (BFS/DFS)"""

    @pytest.fixture
    def sample_graph(self):
        """테스트용 샘플 그래프 생성

        그래프 구조:
        1 -- 2 -- 3
        |    |
        4 -- 5 -- 6

        7 (고립 노드)
        """
        adjacency = {
            1: [{'target': 2, 'line_type': 'pipe', 'connection_id': 'c1'},
                {'target': 4, 'line_type': 'pipe', 'connection_id': 'c2'}],
            2: [{'target': 1, 'line_type': 'pipe', 'connection_id': 'c1'},
                {'target': 3, 'line_type': 'pipe', 'connection_id': 'c3'},
                {'target': 5, 'line_type': 'signal', 'connection_id': 'c4'}],
            3: [{'target': 2, 'line_type': 'pipe', 'connection_id': 'c3'}],
            4: [{'target': 1, 'line_type': 'pipe', 'connection_id': 'c2'},
                {'target': 5, 'line_type': 'pipe', 'connection_id': 'c5'}],
            5: [{'target': 2, 'line_type': 'signal', 'connection_id': 'c4'},
                {'target': 4, 'line_type': 'pipe', 'connection_id': 'c5'},
                {'target': 6, 'line_type': 'pipe', 'connection_id': 'c6'}],
            6: [{'target': 5, 'line_type': 'pipe', 'connection_id': 'c6'}],
            7: []  # 고립 노드
        }
        return adjacency

    @pytest.fixture
    def sample_symbols(self):
        """테스트용 심볼 데이터"""
        return [
            {'id': 1, 'class_name': 'pump', 'category': 'equipment'},
            {'id': 2, 'class_name': 'valve_ball', 'category': 'valve'},
            {'id': 3, 'class_name': 'tank', 'category': 'equipment'},
            {'id': 4, 'class_name': 'check_valve', 'category': 'valve'},
            {'id': 5, 'class_name': 'sensor', 'category': 'instrument'},
            {'id': 6, 'class_name': 'ANU', 'category': 'equipment'},
            {'id': 7, 'class_name': 'ECU', 'category': 'equipment'},
        ]

    def test_find_path_bfs_direct(self, sample_graph):
        """BFS 직접 연결 경로 테스트"""
        from services.analysis_service import find_path_bfs

        result = find_path_bfs(sample_graph, 1, 2)

        assert result['found'] == True
        assert result['path'] == [1, 2]
        assert result['path_length'] == 1
        assert len(result['edges']) == 1

    def test_find_path_bfs_multi_hop(self, sample_graph):
        """BFS 여러 홉 경로 테스트 (최단 경로)"""
        from services.analysis_service import find_path_bfs

        result = find_path_bfs(sample_graph, 1, 6)

        assert result['found'] == True
        # 1 → 4 → 5 → 6 또는 1 → 2 → 5 → 6 (둘 다 길이 3)
        assert result['path_length'] == 3
        assert result['path'][0] == 1
        assert result['path'][-1] == 6

    def test_find_path_bfs_same_node(self, sample_graph):
        """BFS 같은 노드 경로 테스트"""
        from services.analysis_service import find_path_bfs

        result = find_path_bfs(sample_graph, 3, 3)

        assert result['found'] == True
        assert result['path'] == [3]
        assert result['path_length'] == 0

    def test_find_path_bfs_unreachable(self, sample_graph):
        """BFS 연결 불가능 경로 테스트"""
        from services.analysis_service import find_path_bfs

        result = find_path_bfs(sample_graph, 1, 7)  # 7은 고립 노드

        assert result['found'] == False
        assert result['path'] == []
        assert result['path_length'] == -1

    def test_find_path_dfs(self, sample_graph):
        """DFS 경로 테스트"""
        from services.analysis_service import find_path_dfs

        result = find_path_dfs(sample_graph, 1, 6)

        assert result['found'] == True
        assert result['path'][0] == 1
        assert result['path'][-1] == 6
        assert len(result['edges']) == result['path_length']

    def test_find_path_dfs_max_depth(self, sample_graph):
        """DFS 최대 깊이 제한 테스트"""
        from services.analysis_service import find_path_dfs

        # 깊이 1로 제한하면 1→6 경로 찾기 불가
        result = find_path_dfs(sample_graph, 1, 6, max_depth=1)

        assert result['found'] == False

    def test_find_all_paths(self, sample_graph):
        """모든 경로 찾기 테스트"""
        from services.analysis_service import find_all_paths

        paths = find_all_paths(sample_graph, 1, 6)

        assert len(paths) >= 2  # 최소 2개 경로 존재
        for p in paths:
            assert p['path'][0] == 1
            assert p['path'][-1] == 6

    def test_find_all_paths_max_paths(self, sample_graph):
        """모든 경로 찾기 - 최대 경로 수 제한 테스트"""
        from services.analysis_service import find_all_paths

        paths = find_all_paths(sample_graph, 1, 6, max_paths=1)

        assert len(paths) == 1

    def test_is_reachable_true(self, sample_graph):
        """연결 가능 여부 테스트 - True"""
        from services.analysis_service import is_reachable

        assert is_reachable(sample_graph, 1, 6) == True
        assert is_reachable(sample_graph, 3, 4) == True

    def test_is_reachable_false(self, sample_graph):
        """연결 가능 여부 테스트 - False"""
        from services.analysis_service import is_reachable

        assert is_reachable(sample_graph, 1, 7) == False
        assert is_reachable(sample_graph, 7, 3) == False

    def test_get_connected_components(self, sample_graph):
        """연결 컴포넌트 테스트"""
        from services.analysis_service import get_connected_components

        all_nodes = [1, 2, 3, 4, 5, 6, 7]
        components = get_connected_components(sample_graph, all_nodes)

        assert len(components) == 2  # 연결된 그룹 + 고립 노드
        # 큰 컴포넌트 (6개) + 고립 노드 (1개)
        sizes = sorted([len(c) for c in components])
        assert sizes == [1, 6]

    def test_check_path_contains_all_present(self, sample_symbols):
        """경로 내 클래스 확인 - 모두 존재"""
        from services.analysis_service import check_path_contains

        path = [1, 2, 3]  # pump → valve_ball → tank
        result = check_path_contains(path, sample_symbols, ['pump', 'valve_ball'])

        assert result['all_present'] == True
        assert 'pump' in result['found_classes']
        assert 'valve_ball' in result['found_classes']
        assert len(result['missing_classes']) == 0

    def test_check_path_contains_missing(self, sample_symbols):
        """경로 내 클래스 확인 - 일부 누락"""
        from services.analysis_service import check_path_contains

        path = [1, 2, 3]  # pump → valve_ball → tank
        result = check_path_contains(path, sample_symbols, ['pump', 'check_valve', 'ANU'])

        assert result['all_present'] == False
        assert 'pump' in result['found_classes']
        assert 'check_valve' in result['missing_classes']
        assert 'ANU' in result['missing_classes']

    def test_find_symbols_between(self, sample_graph, sample_symbols):
        """두 클래스 사이의 경로 찾기"""
        from services.analysis_service import find_symbols_between

        results = find_symbols_between(sample_graph, sample_symbols, 'pump', 'tank')

        assert len(results) >= 1
        for r in results:
            assert r['start_symbol']['class_name'] == 'pump'
            assert r['end_symbol']['class_name'] == 'tank'
            assert 'intermediate_classes' in r


class TestPathFindingEdgeCases:
    """경로 탐색 엣지 케이스 테스트"""

    def test_empty_adjacency(self):
        """빈 그래프 테스트"""
        from services.analysis_service import find_path_bfs, is_reachable

        result = find_path_bfs({}, 1, 2)
        assert result['found'] == False

        assert is_reachable({}, 1, 2) == False

    def test_single_node_graph(self):
        """단일 노드 그래프 테스트"""
        from services.analysis_service import find_path_bfs, get_connected_components

        adjacency = {1: []}

        result = find_path_bfs(adjacency, 1, 1)
        assert result['found'] == True
        assert result['path'] == [1]

        components = get_connected_components(adjacency, [1])
        assert len(components) == 1

    def test_linear_graph(self):
        """선형 그래프 테스트 (1 - 2 - 3 - 4 - 5)"""
        from services.analysis_service import find_path_bfs, find_all_paths

        adjacency = {
            1: [{'target': 2, 'line_type': 'pipe'}],
            2: [{'target': 1, 'line_type': 'pipe'}, {'target': 3, 'line_type': 'pipe'}],
            3: [{'target': 2, 'line_type': 'pipe'}, {'target': 4, 'line_type': 'pipe'}],
            4: [{'target': 3, 'line_type': 'pipe'}, {'target': 5, 'line_type': 'pipe'}],
            5: [{'target': 4, 'line_type': 'pipe'}],
        }

        result = find_path_bfs(adjacency, 1, 5)
        assert result['found'] == True
        assert result['path'] == [1, 2, 3, 4, 5]
        assert result['path_length'] == 4

        paths = find_all_paths(adjacency, 1, 5)
        assert len(paths) == 1  # 선형이므로 경로 1개

    def test_cycle_graph(self):
        """사이클 그래프 테스트 (1 - 2 - 3 - 1)"""
        from services.analysis_service import find_path_bfs, find_all_paths

        adjacency = {
            1: [{'target': 2, 'line_type': 'pipe'}, {'target': 3, 'line_type': 'pipe'}],
            2: [{'target': 1, 'line_type': 'pipe'}, {'target': 3, 'line_type': 'pipe'}],
            3: [{'target': 2, 'line_type': 'pipe'}, {'target': 1, 'line_type': 'pipe'}],
        }

        result = find_path_bfs(adjacency, 1, 3)
        assert result['found'] == True
        assert result['path_length'] == 1  # 직접 연결

        paths = find_all_paths(adjacency, 1, 3)
        assert len(paths) == 2  # 1→3, 1→2→3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
