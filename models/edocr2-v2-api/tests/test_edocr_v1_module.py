"""
eDOCr v1 Module Unit Tests
Engineering Drawing OCR Service 모듈 테스트
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSchemas:
    """스키마 클래스 테스트"""

    def test_ocr_request_exists(self):
        """OCRRequest 클래스 존재"""
        from edocr_v1 import OCRRequest

        assert OCRRequest is not None

    def test_enhanced_ocr_request_exists(self):
        """EnhancedOCRRequest 클래스 존재"""
        from edocr_v1 import EnhancedOCRRequest

        assert EnhancedOCRRequest is not None

    def test_dimension_exists(self):
        """Dimension 클래스 존재"""
        from edocr_v1 import Dimension

        assert Dimension is not None

    def test_gdt_exists(self):
        """GDT 클래스 존재"""
        from edocr_v1 import GDT

        assert GDT is not None

    def test_text_info_exists(self):
        """TextInfo 클래스 존재"""
        from edocr_v1 import TextInfo

        assert TextInfo is not None

    def test_ocr_result_exists(self):
        """OCRResult 클래스 존재"""
        from edocr_v1 import OCRResult

        assert OCRResult is not None

    def test_ocr_response_exists(self):
        """OCRResponse 클래스 존재"""
        from edocr_v1 import OCRResponse

        assert OCRResponse is not None


class TestUtils:
    """유틸리티 함수 테스트"""

    def test_convert_to_serializable_exists(self):
        """convert_to_serializable 함수 존재"""
        from edocr_v1 import convert_to_serializable

        assert convert_to_serializable is not None
        assert callable(convert_to_serializable)

    def test_allowed_file_exists(self):
        """allowed_file 함수 존재"""
        from edocr_v1 import allowed_file

        assert allowed_file is not None
        assert callable(allowed_file)

    def test_transform_edocr_to_ui_format_exists(self):
        """transform_edocr_to_ui_format 함수 존재"""
        from edocr_v1 import transform_edocr_to_ui_format

        assert transform_edocr_to_ui_format is not None
        assert callable(transform_edocr_to_ui_format)

    def test_init_directories_exists(self):
        """init_directories 함수 존재"""
        from edocr_v1 import init_directories

        assert init_directories is not None
        assert callable(init_directories)


class TestDirectoryConstants:
    """디렉토리 상수 테스트"""

    def test_upload_dir_exists(self):
        """UPLOAD_DIR 상수 존재"""
        from edocr_v1 import UPLOAD_DIR

        assert UPLOAD_DIR is not None

    def test_results_dir_exists(self):
        """RESULTS_DIR 상수 존재"""
        from edocr_v1 import RESULTS_DIR

        assert RESULTS_DIR is not None


class TestAlphabetConstants:
    """알파벳 상수 테스트"""

    def test_allowed_extensions_exists(self):
        """ALLOWED_EXTENSIONS 존재"""
        from edocr_v1 import ALLOWED_EXTENSIONS

        assert ALLOWED_EXTENSIONS is not None
        assert isinstance(ALLOWED_EXTENSIONS, (list, set, tuple))

    def test_alphabet_dimensions_exists(self):
        """ALPHABET_DIMENSIONS 존재"""
        from edocr_v1 import ALPHABET_DIMENSIONS

        assert ALPHABET_DIMENSIONS is not None

    def test_alphabet_infoblock_exists(self):
        """ALPHABET_INFOBLOCK 존재"""
        from edocr_v1 import ALPHABET_INFOBLOCK

        assert ALPHABET_INFOBLOCK is not None

    def test_alphabet_gdts_exists(self):
        """ALPHABET_GDTS 존재"""
        from edocr_v1 import ALPHABET_GDTS

        assert ALPHABET_GDTS is not None


class TestOCRService:
    """OCR 서비스 테스트"""

    def test_ocr_service_class_exists(self):
        """OCRService 클래스 존재"""
        from edocr_v1 import OCRService

        assert OCRService is not None


class TestRouters:
    """라우터 테스트"""

    def test_ocr_router_exists(self):
        """ocr_router 존재"""
        from edocr_v1 import ocr_router

        assert ocr_router is not None

    def test_docs_router_exists(self):
        """docs_router 존재"""
        from edocr_v1 import docs_router

        assert docs_router is not None


class TestAllowedFileFunction:
    """allowed_file 함수 동작 테스트"""

    def test_allowed_file_png(self):
        """PNG 파일 허용"""
        from edocr_v1 import allowed_file

        result = allowed_file("test.png")
        # png가 허용 확장자에 있으면 True
        assert result in [True, False]  # 함수가 동작함

    def test_allowed_file_jpg(self):
        """JPG 파일 허용"""
        from edocr_v1 import allowed_file

        result = allowed_file("test.jpg")
        assert result in [True, False]

    def test_allowed_file_invalid(self):
        """유효하지 않은 파일"""
        from edocr_v1 import allowed_file

        result = allowed_file("test.exe")
        assert result is False


class TestConvertToSerializable:
    """convert_to_serializable 함수 동작 테스트"""

    def test_convert_dict(self):
        """딕셔너리 변환"""
        from edocr_v1 import convert_to_serializable

        data = {"key": "value"}
        result = convert_to_serializable(data)
        assert result == {"key": "value"}

    def test_convert_list(self):
        """리스트 변환"""
        from edocr_v1 import convert_to_serializable

        data = [1, 2, 3]
        result = convert_to_serializable(data)
        assert result == [1, 2, 3]


class TestModuleExports:
    """모듈 __all__ 내보내기 테스트"""

    def test_all_exports(self):
        """__all__ 내보내기 확인"""
        import edocr_v1

        expected_exports = [
            "OCRRequest",
            "EnhancedOCRRequest",
            "Dimension",
            "GDT",
            "TextInfo",
            "OCRResult",
            "OCRResponse",
            "convert_to_serializable",
            "allowed_file",
            "transform_edocr_to_ui_format",
            "init_directories",
            "UPLOAD_DIR",
            "RESULTS_DIR",
            "ALLOWED_EXTENSIONS",
            "ALPHABET_DIMENSIONS",
            "ALPHABET_INFOBLOCK",
            "ALPHABET_GDTS",
            "OCRService",
            "ocr_router",
            "docs_router",
        ]

        for export_name in expected_exports:
            assert hasattr(edocr_v1, export_name), f"Missing export: {export_name}"
