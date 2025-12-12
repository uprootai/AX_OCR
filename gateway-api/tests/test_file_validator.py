"""
파일 업로드 검증 테스트

매직 바이트 검증 및 확장자 검증 테스트
"""
import pytest
from utils.file_validator import (
    validate_file,
    validate_image_file,
    validate_extension,
    validate_magic_bytes,
    get_file_info,
    detect_file_type,
    ALLOWED_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS
)


class TestValidateExtension:
    """확장자 검증 테스트"""

    def test_valid_image_extensions(self):
        """유효한 이미지 확장자"""
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"]
        for ext in valid_extensions:
            is_valid, error = validate_extension(f"test{ext}")
            assert is_valid is True, f"Extension {ext} should be valid"
            assert error is None

    def test_valid_document_extensions(self):
        """유효한 문서 확장자"""
        is_valid, error = validate_extension("document.pdf")
        assert is_valid is True
        assert error is None

    def test_invalid_extension(self):
        """무효한 확장자"""
        is_valid, error = validate_extension("malware.exe")
        assert is_valid is False
        assert "지원하지 않는 파일 형식" in error

    def test_no_extension(self):
        """확장자 없음"""
        is_valid, error = validate_extension("noextension")
        assert is_valid is False
        assert "확장자가 없습니다" in error

    def test_empty_filename(self):
        """빈 파일명"""
        is_valid, error = validate_extension("")
        assert is_valid is False
        assert "비어있습니다" in error

    def test_case_insensitive(self):
        """대소문자 구분 없음"""
        is_valid, error = validate_extension("TEST.JPG")
        assert is_valid is True

        is_valid, error = validate_extension("TEST.PNG")
        assert is_valid is True


class TestValidateMagicBytes:
    """매직 바이트 검증 테스트"""

    def test_valid_jpeg(self):
        """유효한 JPEG 파일"""
        # JPEG 매직 바이트: FF D8 FF
        content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.jpg", content)
        assert is_valid is True
        assert error is None

    def test_valid_png(self):
        """유효한 PNG 파일"""
        # PNG 매직 바이트: 89 50 4E 47 0D 0A 1A 0A
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.png", content)
        assert is_valid is True
        assert error is None

    def test_valid_gif87a(self):
        """유효한 GIF87a 파일"""
        content = b"GIF87a" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.gif", content)
        assert is_valid is True

    def test_valid_gif89a(self):
        """유효한 GIF89a 파일"""
        content = b"GIF89a" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.gif", content)
        assert is_valid is True

    def test_valid_bmp(self):
        """유효한 BMP 파일"""
        content = b"BM" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.bmp", content)
        assert is_valid is True

    def test_valid_tiff_little_endian(self):
        """유효한 TIFF 파일 (Little Endian)"""
        content = b"\x49\x49\x2A\x00" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.tiff", content)
        assert is_valid is True

    def test_valid_tiff_big_endian(self):
        """유효한 TIFF 파일 (Big Endian)"""
        content = b"\x4D\x4D\x00\x2A" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.tif", content)
        assert is_valid is True

    def test_valid_pdf(self):
        """유효한 PDF 파일"""
        content = b"%PDF-1.4" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("document.pdf", content)
        assert is_valid is True

    def test_extension_content_mismatch(self):
        """확장자와 내용 불일치"""
        # PNG 확장자에 JPEG 내용
        jpeg_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.png", jpeg_content)
        assert is_valid is False
        assert "일치하지 않습니다" in error

    def test_empty_content(self):
        """빈 내용"""
        is_valid, error = validate_magic_bytes("test.jpg", b"")
        assert is_valid is False
        assert "비어있습니다" in error

    def test_unknown_magic_bytes(self):
        """알 수 없는 매직 바이트"""
        content = b"\x00\x00\x00\x00" + b"\x00" * 100
        is_valid, error = validate_magic_bytes("test.jpg", content)
        assert is_valid is False
        assert "알 수 없는 파일 형식" in error


class TestValidateFile:
    """종합 검증 테스트"""

    def test_valid_jpeg_file(self):
        """유효한 JPEG 파일 종합 검증"""
        content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        is_valid, error = validate_file("photo.jpg", content)
        assert is_valid is True
        assert error is None

    def test_invalid_extension_fails_first(self):
        """확장자 검증 실패 시 매직 바이트 검증 안함"""
        content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100  # Valid JPEG content
        is_valid, error = validate_file("malware.exe", content)
        assert is_valid is False
        assert "지원하지 않는 파일 형식" in error


class TestValidateImageFile:
    """이미지 파일 전용 검증 테스트"""

    def test_valid_image(self):
        """유효한 이미지"""
        content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        is_valid, error = validate_image_file("photo.jpg", content)
        assert is_valid is True

    def test_pdf_not_allowed(self):
        """PDF는 이미지 검증에서 거부"""
        content = b"%PDF-1.4" + b"\x00" * 100
        is_valid, error = validate_image_file("document.pdf", content)
        assert is_valid is False
        assert "이미지 파일만 허용" in error


class TestDetectFileType:
    """파일 타입 감지 테스트"""

    def test_detect_jpeg(self):
        """JPEG 감지"""
        header = b"\xFF\xD8\xFF\xE0\x00"
        assert detect_file_type(header) == "jpeg"

    def test_detect_png(self):
        """PNG 감지"""
        header = b"\x89PNG\r\n\x1a\n"
        assert detect_file_type(header) == "png"

    def test_detect_gif(self):
        """GIF 감지"""
        assert detect_file_type(b"GIF87a") == "gif"
        assert detect_file_type(b"GIF89a") == "gif"

    def test_detect_unknown(self):
        """알 수 없는 형식"""
        header = b"\x00\x00\x00\x00"
        assert detect_file_type(header) is None


class TestGetFileInfo:
    """파일 정보 조회 테스트"""

    def test_valid_file_info(self):
        """유효한 파일 정보"""
        content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        info = get_file_info("photo.jpg", content)

        assert info["filename"] == "photo.jpg"
        assert info["extension"] == ".jpg"
        assert info["size_bytes"] == 104
        assert info["detected_type"] == "jpeg"
        assert info["is_valid"] is True
        assert info["error"] is None

    def test_invalid_file_info(self):
        """무효한 파일 정보"""
        # PNG 확장자에 JPEG 내용
        content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        info = get_file_info("fake.png", content)

        assert info["filename"] == "fake.png"
        assert info["extension"] == ".png"
        assert info["detected_type"] == "jpeg"
        assert info["is_valid"] is False
        assert "일치하지 않습니다" in info["error"]


class TestConstants:
    """상수 테스트"""

    def test_allowed_extensions_includes_images(self):
        """이미지 확장자 포함"""
        for ext in [".jpg", ".jpeg", ".png", ".gif"]:
            assert ext in ALLOWED_EXTENSIONS

    def test_allowed_extensions_includes_pdf(self):
        """PDF 확장자 포함"""
        assert ".pdf" in ALLOWED_EXTENSIONS

    def test_allowed_image_extensions_no_pdf(self):
        """이미지 확장자에 PDF 미포함"""
        assert ".pdf" not in ALLOWED_IMAGE_EXTENSIONS
