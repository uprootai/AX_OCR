"""
DWG Parsing Tests
DWG/DXF 파싱 기능 테스트
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestDWGServiceImport:
    """DWG 서비스 모듈 임포트 테스트"""

    def test_import_dwg_service(self):
        """dwg_service 모듈 임포트"""
        from services import dwg_service
        assert dwg_service is not None

    def test_import_parse_dxf(self):
        """parse_dxf 함수 임포트"""
        from services.dwg_service import parse_dxf
        assert callable(parse_dxf)

    def test_import_parse_dwg(self):
        """parse_dwg 함수 임포트"""
        from services.dwg_service import parse_dwg
        assert callable(parse_dwg)

    def test_import_extract_pid_elements(self):
        """extract_pid_elements 함수 임포트"""
        from services.dwg_service import extract_pid_elements
        assert callable(extract_pid_elements)

    def test_import_get_dwg_info(self):
        """get_dwg_info 함수 임포트"""
        from services.dwg_service import get_dwg_info
        assert callable(get_dwg_info)


class TestODADetection:
    """ODA File Converter 검출 테스트"""

    def test_is_oda_available_function_exists(self):
        """is_oda_available 함수 존재"""
        from services.dwg_service import is_oda_available
        assert callable(is_oda_available)

    def test_find_oda_converter_function_exists(self):
        """find_oda_converter 함수 존재"""
        from services.dwg_service import find_oda_converter
        assert callable(find_oda_converter)

    def test_get_dwg_info_returns_dict(self):
        """get_dwg_info가 올바른 형식 반환"""
        from services.dwg_service import get_dwg_info
        info = get_dwg_info()

        assert isinstance(info, dict)
        assert "oda_available" in info
        assert "supported_formats" in info
        assert "output_entities" in info
        assert "install_oda" in info

    def test_supported_formats_include_dwg_dxf(self):
        """지원 포맷에 DWG, DXF 포함"""
        from services.dwg_service import get_dwg_info
        info = get_dwg_info()

        assert "DWG" in info["supported_formats"]
        assert "DXF" in info["supported_formats"]


class TestDXFParsing:
    """DXF 파싱 테스트 (ezdxf 사용)"""

    def test_parse_dxf_nonexistent_file(self):
        """존재하지 않는 파일 처리"""
        from services.dwg_service import parse_dxf
        result = parse_dxf("/nonexistent/path/file.dxf")

        assert "error" in result
        # ezdxf 미설치 또는 파일 없음 에러
        assert "not found" in result["error"].lower() or "ezdxf" in result["error"].lower()

    def test_parse_dxf_with_mock_doc(self):
        """DXF 파싱 결과 구조 확인 (모킹)"""
        from services.dwg_service import extract_metadata, extract_layers, extract_blocks

        # 메타데이터 추출 함수 테스트
        mock_doc = MagicMock()
        mock_doc.dxfversion = "AC1032"
        mock_doc.encoding = "utf-8"
        mock_doc.header.get.side_effect = lambda key, default: {
            "$INSUNITS": 4,
            "$EXTMIN": (0, 0, 0),
            "$EXTMAX": (1000, 1000, 0)
        }.get(key, default)

        metadata = extract_metadata(mock_doc)

        assert metadata["version"] == "AC1032"
        assert metadata["encoding"] == "utf-8"
        assert metadata["units"] == 4


class TestEntityExtraction:
    """엔티티 추출 함수 테스트"""

    def test_extract_line(self):
        """LINE 엔티티 추출"""
        from services.dwg_service import extract_line

        mock_entity = MagicMock()
        mock_entity.dxf.layer = "PIPE"
        mock_entity.dxf.start.x = 0
        mock_entity.dxf.start.y = 0
        mock_entity.dxf.end.x = 100
        mock_entity.dxf.end.y = 100
        mock_entity.dxf.color = 1
        mock_entity.dxf.linetype = "CONTINUOUS"

        result = extract_line(mock_entity)

        assert result["type"] == "LINE"
        assert result["layer"] == "PIPE"
        assert result["start"] == [0, 0]
        assert result["end"] == [100, 100]

    def test_extract_circle(self):
        """CIRCLE 엔티티 추출"""
        from services.dwg_service import extract_circle

        mock_entity = MagicMock()
        mock_entity.dxf.layer = "VALVE"
        mock_entity.dxf.center.x = 50
        mock_entity.dxf.center.y = 50
        mock_entity.dxf.radius = 25
        mock_entity.dxf.color = 2

        result = extract_circle(mock_entity)

        assert result["type"] == "CIRCLE"
        assert result["layer"] == "VALVE"
        assert result["center"] == [50, 50]
        assert result["radius"] == 25

    def test_extract_text(self):
        """TEXT 엔티티 추출"""
        from services.dwg_service import extract_text

        mock_entity = MagicMock()
        mock_entity.dxf.layer = "TEXT"
        mock_entity.dxf.text = "V-001"
        mock_entity.dxf.insert.x = 100
        mock_entity.dxf.insert.y = 200
        mock_entity.dxf.height = 10
        mock_entity.dxf.rotation = 0
        mock_entity.dxf.color = 7

        result = extract_text(mock_entity)

        assert result["type"] == "TEXT"
        assert result["text"] == "V-001"
        assert result["insert"] == [100, 200]
        assert result["height"] == 10

    def test_extract_insert(self):
        """INSERT (블록 참조) 엔티티 추출"""
        from services.dwg_service import extract_insert

        mock_entity = MagicMock()
        mock_entity.dxf.layer = "SYMBOL"
        mock_entity.dxf.name = "CHECK_VALVE"
        mock_entity.dxf.insert.x = 300
        mock_entity.dxf.insert.y = 400
        mock_entity.dxf.xscale = 1.0
        mock_entity.dxf.yscale = 1.0
        mock_entity.dxf.rotation = 90
        mock_entity.dxf.color = 3

        result = extract_insert(mock_entity)

        assert result["type"] == "INSERT"
        assert result["block_name"] == "CHECK_VALVE"
        assert result["insert"] == [300, 400]
        assert result["rotation"] == 90


class TestPIDElementExtraction:
    """P&ID 요소 추출 테스트"""

    def test_extract_pid_elements_with_error(self):
        """에러가 있는 파싱 데이터 처리"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {"error": "Test error"}
        result = extract_pid_elements(parsed_data)

        assert "error" in result

    def test_extract_pid_elements_empty_data(self):
        """빈 데이터 처리"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {"entities": {}}
        result = extract_pid_elements(parsed_data)

        assert "lines" in result
        assert "symbols" in result
        assert "texts" in result
        assert result["statistics"]["lines"] == 0
        assert result["statistics"]["symbols"] == 0
        assert result["statistics"]["texts"] == 0

    def test_extract_pid_elements_with_lines(self):
        """라인 추출"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {
            "entities": {
                "lines": [
                    {
                        "type": "LINE",
                        "start": [0, 0],
                        "end": [100, 100],
                        "layer": "PIPE",
                        "linetype": "CONTINUOUS"
                    }
                ],
                "polylines": [],
                "circles": [],
                "texts": [],
                "mtexts": [],
                "inserts": []
            }
        }

        result = extract_pid_elements(parsed_data)

        assert len(result["lines"]) == 1
        assert result["lines"][0]["start"] == [0, 0]
        assert result["lines"][0]["end"] == [100, 100]

    def test_extract_pid_elements_with_polyline(self):
        """폴리라인 추출 (세그먼트로 분해)"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {
            "entities": {
                "lines": [],
                "polylines": [
                    {
                        "type": "LWPOLYLINE",
                        "points": [[0, 0], [100, 0], [100, 100]],
                        "is_closed": False,
                        "layer": "PIPE",
                        "linetype": "CONTINUOUS"
                    }
                ],
                "circles": [],
                "texts": [],
                "mtexts": [],
                "inserts": []
            }
        }

        result = extract_pid_elements(parsed_data)

        # 3개 점 → 2개 세그먼트
        assert len(result["lines"]) == 2

    def test_extract_pid_elements_with_closed_polyline(self):
        """닫힌 폴리라인 추출"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {
            "entities": {
                "lines": [],
                "polylines": [
                    {
                        "type": "LWPOLYLINE",
                        "points": [[0, 0], [100, 0], [100, 100]],
                        "is_closed": True,
                        "layer": "PIPE",
                        "linetype": "CONTINUOUS"
                    }
                ],
                "circles": [],
                "texts": [],
                "mtexts": [],
                "inserts": []
            }
        }

        result = extract_pid_elements(parsed_data)

        # 3개 점 + 닫힘 → 3개 세그먼트
        assert len(result["lines"]) == 3

    def test_extract_pid_elements_with_symbols(self):
        """심볼 (블록 참조 + 원) 추출"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {
            "entities": {
                "lines": [],
                "polylines": [],
                "circles": [
                    {
                        "type": "CIRCLE",
                        "center": [50, 50],
                        "radius": 10,
                        "layer": "VALVE"
                    }
                ],
                "texts": [],
                "mtexts": [],
                "inserts": [
                    {
                        "type": "INSERT",
                        "block_name": "PUMP",
                        "insert": [200, 200],
                        "scale": [1, 1],
                        "rotation": 0,
                        "layer": "EQUIPMENT"
                    }
                ]
            }
        }

        result = extract_pid_elements(parsed_data)

        assert len(result["symbols"]) == 2

        # 심볼 타입 확인 (순서 무관)
        symbol_types = {s["type"] for s in result["symbols"]}
        assert "block_reference" in symbol_types
        assert "circle" in symbol_types

        # 각 심볼 타입별 확인
        block_refs = [s for s in result["symbols"] if s["type"] == "block_reference"]
        circles = [s for s in result["symbols"] if s["type"] == "circle"]

        assert len(block_refs) == 1
        assert block_refs[0]["block_name"] == "PUMP"
        assert len(circles) == 1
        assert circles[0]["radius"] == 10

    def test_extract_pid_elements_with_texts(self):
        """텍스트 추출"""
        from services.dwg_service import extract_pid_elements

        parsed_data = {
            "entities": {
                "lines": [],
                "polylines": [],
                "circles": [],
                "texts": [
                    {
                        "type": "TEXT",
                        "text": "V-001",
                        "insert": [100, 100],
                        "height": 5,
                        "layer": "TEXT"
                    }
                ],
                "mtexts": [
                    {
                        "type": "MTEXT",
                        "text": "PUMP-001\\PCENTRIFUGAL",
                        "insert": [200, 200],
                        "char_height": 5,
                        "layer": "TEXT"
                    }
                ],
                "inserts": []
            }
        }

        result = extract_pid_elements(parsed_data)

        assert len(result["texts"]) == 2
        assert result["texts"][0]["content"] == "V-001"
        assert result["texts"][1]["content"] == "PUMP-001\\PCENTRIFUGAL"


class TestDWGRouterEndpoints:
    """DWG 라우터 엔드포인트 테스트"""

    def test_router_import(self):
        """dwg_router 임포트"""
        from routers.dwg_router import router
        assert router is not None

    def test_router_prefix(self):
        """라우터 prefix 확인"""
        from routers.dwg_router import router
        assert router.prefix == "/api/v1/dwg"

    def test_dwg_info_endpoint_exists(self):
        """DWG info 엔드포인트 존재"""
        from routers.dwg_router import dwg_info
        assert callable(dwg_info)

    def test_parse_dwg_file_endpoint_exists(self):
        """DWG parse 엔드포인트 존재"""
        from routers.dwg_router import parse_dwg_file
        assert callable(parse_dwg_file)

    def test_parse_dxf_file_endpoint_exists(self):
        """DXF parse 엔드포인트 존재"""
        from routers.dwg_router import parse_dxf_file
        assert callable(parse_dxf_file)

    def test_extract_pid_endpoint_exists(self):
        """P&ID 추출 엔드포인트 존재"""
        from routers.dwg_router import extract_pid_from_file
        assert callable(extract_pid_from_file)


class TestDXFCreation:
    """실제 DXF 파일 생성 및 파싱 테스트"""

    @pytest.fixture
    def sample_dxf_file(self):
        """테스트용 간단한 DXF 파일 생성"""
        try:
            import ezdxf
        except ImportError:
            pytest.skip("ezdxf not installed")

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # 라인 추가
        msp.add_line((0, 0), (100, 100), dxfattribs={"layer": "PIPE"})
        msp.add_line((100, 100), (200, 100), dxfattribs={"layer": "PIPE"})

        # 원 추가
        msp.add_circle((50, 50), radius=10, dxfattribs={"layer": "VALVE"})

        # 텍스트 추가
        msp.add_text("V-001", dxfattribs={"layer": "TEXT", "height": 5}).set_placement((100, 100))

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            temp_path = f.name
            doc.saveas(temp_path)

        yield temp_path

        # 정리
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_parse_real_dxf_file(self, sample_dxf_file):
        """실제 DXF 파일 파싱"""
        from services.dwg_service import parse_dxf

        result = parse_dxf(sample_dxf_file)

        assert "error" not in result
        assert "metadata" in result
        assert "entities" in result
        assert "statistics" in result

        # 엔티티 확인
        assert result["statistics"]["lines"] >= 2
        assert result["statistics"]["circles"] >= 1
        assert result["statistics"]["texts"] >= 1

    def test_extract_pid_from_real_dxf(self, sample_dxf_file):
        """실제 DXF에서 P&ID 요소 추출"""
        from services.dwg_service import parse_dxf, extract_pid_elements

        parsed_data = parse_dxf(sample_dxf_file)
        result = extract_pid_elements(parsed_data)

        assert "lines" in result
        assert "symbols" in result
        assert "texts" in result

        # 라인 2개
        assert len(result["lines"]) >= 2

        # 원 1개 → 심볼 후보
        assert len(result["symbols"]) >= 1

        # 텍스트 1개
        assert len(result["texts"]) >= 1


class TestDWGConversion:
    """DWG 변환 테스트 (ODA 필요)"""

    def test_convert_without_oda(self):
        """ODA 없이 변환 시도"""
        from services.dwg_service import convert_dwg_to_dxf, is_oda_available

        if is_oda_available():
            pytest.skip("ODA is available, skipping this test")

        success, dxf_path, error = convert_dwg_to_dxf("/nonexistent/file.dwg")

        assert success is False
        assert "ODA" in error or "not found" in error.lower()

    def test_convert_nonexistent_file_with_oda(self):
        """존재하지 않는 DWG 파일 변환"""
        from services.dwg_service import convert_dwg_to_dxf, is_oda_available

        if not is_oda_available():
            pytest.skip("ODA not available")

        success, dxf_path, error = convert_dwg_to_dxf("/nonexistent/file.dwg")

        assert success is False
        assert "not found" in error.lower()


class TestAPIIntegration:
    """API 통합 테스트 (실행 중인 서버 대상)"""

    def test_dwg_info_api(self):
        """GET /api/v1/dwg/info 테스트"""
        import httpx

        try:
            response = httpx.get("http://localhost:5018/api/v1/dwg/info", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "oda_available" in data
            assert "supported_formats" in data
        except httpx.ConnectError:
            pytest.skip("pid-analyzer-api server not running")

    def test_dwg_layers_api(self):
        """GET /api/v1/dwg/layers 테스트"""
        import httpx

        try:
            response = httpx.get("http://localhost:5018/api/v1/dwg/layers", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "common_layers" in data
            assert "bwms_specific" in data
        except httpx.ConnectError:
            pytest.skip("pid-analyzer-api server not running")
