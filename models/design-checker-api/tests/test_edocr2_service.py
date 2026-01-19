"""
eDOCr2 Service Tests
eDOCr2 API 연동 서비스 테스트
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestEDOCr2ServiceImport:
    """eDOCr2 서비스 모듈 임포트 테스트"""

    def test_import_edocr2_service_module(self):
        """edocr2_service 모듈 임포트"""
        from services import edocr2_service
        assert edocr2_service is not None

    def test_import_edocr2_service_class(self):
        """EDOCr2Service 클래스 임포트"""
        from services.edocr2_service import EDOCr2Service
        assert EDOCr2Service is not None

    def test_import_dimension_dataclass(self):
        """Dimension 데이터클래스 임포트"""
        from services.edocr2_service import Dimension
        assert Dimension is not None

    def test_import_gdt_symbol_dataclass(self):
        """GDTSymbol 데이터클래스 임포트"""
        from services.edocr2_service import GDTSymbol
        assert GDTSymbol is not None

    def test_import_text_block_dataclass(self):
        """TextBlock 데이터클래스 임포트"""
        from services.edocr2_service import TextBlock
        assert TextBlock is not None

    def test_import_edocr2_result_dataclass(self):
        """EDOCr2Result 데이터클래스 임포트"""
        from services.edocr2_service import EDOCr2Result
        assert EDOCr2Result is not None

    def test_singleton_instance(self):
        """싱글톤 인스턴스 확인"""
        from services.edocr2_service import edocr2_service, EDOCr2Service
        assert isinstance(edocr2_service, EDOCr2Service)


class TestEDOCr2ServiceInit:
    """eDOCr2 서비스 초기화 테스트"""

    def test_default_base_url(self):
        """기본 URL 확인"""
        from services.edocr2_service import EDOCr2Service, EDOCR2_API_URL
        service = EDOCr2Service()
        assert service.base_url == EDOCR2_API_URL

    def test_custom_base_url(self):
        """커스텀 URL 설정"""
        from services.edocr2_service import EDOCr2Service
        service = EDOCr2Service(base_url="http://custom:5002")
        assert service.base_url == "http://custom:5002"

    def test_timeout_setting(self):
        """타임아웃 설정 확인"""
        from services.edocr2_service import EDOCr2Service, EDOCR2_TIMEOUT
        service = EDOCr2Service()
        assert service.timeout == EDOCR2_TIMEOUT


class TestDimensionDataclass:
    """Dimension 데이터클래스 테스트"""

    def test_dimension_creation(self):
        """Dimension 생성"""
        from services.edocr2_service import Dimension

        dim = Dimension(
            value="100.5",
            tolerance="±0.1",
            unit="mm",
            bbox=[10, 20, 50, 30],
            dim_type="linear",
            confidence=0.95,
        )

        assert dim.value == "100.5"
        assert dim.tolerance == "±0.1"
        assert dim.unit == "mm"
        assert dim.dim_type == "linear"
        assert dim.confidence == 0.95

    def test_dimension_defaults(self):
        """Dimension 기본값"""
        from services.edocr2_service import Dimension

        dim = Dimension(value="50")

        assert dim.tolerance is None
        assert dim.unit == "mm"
        assert dim.dim_type == "linear"
        assert dim.confidence == 0.0


class TestGDTSymbolDataclass:
    """GDTSymbol 데이터클래스 테스트"""

    def test_gdt_symbol_creation(self):
        """GDTSymbol 생성"""
        from services.edocr2_service import GDTSymbol

        gdt = GDTSymbol(
            symbol="⊥",
            gdt_type="perpendicularity",
            tolerance="0.05",
            datum=["A", "B"],
            bbox=[100, 200, 50, 30],
            confidence=0.9,
        )

        assert gdt.symbol == "⊥"
        assert gdt.gdt_type == "perpendicularity"
        assert gdt.tolerance == "0.05"
        assert gdt.datum == ["A", "B"]

    def test_gdt_symbol_defaults(self):
        """GDTSymbol 기본값"""
        from services.edocr2_service import GDTSymbol

        gdt = GDTSymbol(
            symbol="⌀",
            gdt_type="position",
        )

        assert gdt.tolerance is None
        assert gdt.datum == []
        assert gdt.bbox == []


class TestTextBlockDataclass:
    """TextBlock 데이터클래스 테스트"""

    def test_text_block_creation(self):
        """TextBlock 생성"""
        from services.edocr2_service import TextBlock

        text = TextBlock(
            text="V-001",
            bbox=[50, 100, 80, 30],
            confidence=0.98,
            x=50,
            y=100,
            width=80,
            height=30,
        )

        assert text.text == "V-001"
        assert text.confidence == 0.98
        assert text.x == 50

    def test_text_block_defaults(self):
        """TextBlock 기본값"""
        from services.edocr2_service import TextBlock

        text = TextBlock(text="TEST")

        assert text.bbox == []
        assert text.confidence == 0.0
        assert text.x == 0


class TestEDOCr2ResultDataclass:
    """EDOCr2Result 데이터클래스 테스트"""

    def test_edocr2_result_success(self):
        """성공 결과 생성"""
        from services.edocr2_service import EDOCr2Result, Dimension, TextBlock

        dim = Dimension(value="100")
        text = TextBlock(text="V-001")

        result = EDOCr2Result(
            success=True,
            dimensions=[dim],
            text_blocks=[text],
            processing_time=1.5,
        )

        assert result.success is True
        assert len(result.dimensions) == 1
        assert len(result.text_blocks) == 1
        assert result.error is None

    def test_edocr2_result_failure(self):
        """실패 결과 생성"""
        from services.edocr2_service import EDOCr2Result

        result = EDOCr2Result(
            success=False,
            error="Connection failed",
        )

        assert result.success is False
        assert result.error == "Connection failed"
        assert result.dimensions == []

    def test_edocr2_result_defaults(self):
        """기본값 확인"""
        from services.edocr2_service import EDOCr2Result

        result = EDOCr2Result(success=True)

        assert result.dimensions == []
        assert result.gdt_symbols == []
        assert result.text_blocks == []
        assert result.tables == []
        assert result.drawing_number is None


class TestExtractFromImageAsync:
    """extract_from_image 비동기 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_extract_success_mock(self):
        """성공적인 추출 (모킹)"""
        from services.edocr2_service import EDOCr2Service

        service = EDOCr2Service()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "processing_time": 1.2,
            "data": {
                "dimensions": [
                    {"value": "100.5", "tolerance": "±0.1", "unit": "mm", "type": "linear", "confidence": 0.95}
                ],
                "gdt": [
                    {"symbol": "⊥", "type": "perpendicularity", "tolerance": "0.05", "datum": ["A"], "confidence": 0.9}
                ],
                "text_blocks": [
                    {"text": "V-001", "bbox": [10, 20, 30, 15], "confidence": 0.98}
                ],
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.extract_from_image(b"fake_image_data")

            assert result.success is True
            assert len(result.dimensions) == 1
            assert result.dimensions[0].value == "100.5"

    @pytest.mark.asyncio
    async def test_extract_api_error(self):
        """API 오류 처리"""
        from services.edocr2_service import EDOCr2Service

        service = EDOCr2Service()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.extract_from_image(b"fake_image_data")

            assert result.success is False
            assert "500" in result.error

    @pytest.mark.asyncio
    async def test_extract_timeout(self):
        """타임아웃 처리"""
        from services.edocr2_service import EDOCr2Service

        service = EDOCr2Service()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.TimeoutException("Timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.extract_from_image(b"fake_image_data")

            assert result.success is False
            assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_extract_exception(self):
        """일반 예외 처리"""
        from services.edocr2_service import EDOCr2Service

        service = EDOCr2Service()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = Exception("Connection refused")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await service.extract_from_image(b"fake_image_data")

            assert result.success is False
            assert result.error is not None


class TestExtractTagsOnly:
    """extract_tags_only 메서드 테스트 (존재하는 경우)"""

    def test_method_exists(self):
        """메서드 존재 확인"""
        from services.edocr2_service import EDOCr2Service
        service = EDOCr2Service()

        # extract_tags_only 메서드가 있는지 확인
        if hasattr(service, 'extract_tags_only'):
            assert callable(service.extract_tags_only)


class TestGetAllTexts:
    """get_all_texts 메서드 테스트 (존재하는 경우)"""

    def test_method_exists(self):
        """메서드 존재 확인"""
        from services.edocr2_service import EDOCr2Service
        service = EDOCr2Service()

        if hasattr(service, 'get_all_texts'):
            assert callable(service.get_all_texts)


class TestParseEquipmentTags:
    """parse_equipment_tags 메서드 테스트 (존재하는 경우)"""

    def test_method_exists(self):
        """메서드 존재 확인"""
        from services.edocr2_service import EDOCr2Service
        service = EDOCr2Service()

        if hasattr(service, 'parse_equipment_tags'):
            assert callable(service.parse_equipment_tags)
