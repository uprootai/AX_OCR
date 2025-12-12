"""
파일 업로드 검증 유틸리티

매직 바이트를 확인하여 파일 형식을 검증합니다.
확장자만 변경한 잘못된 파일 업로드를 방지합니다.
"""

from typing import Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 지원하는 파일 형식의 매직 바이트
MAGIC_BYTES = {
    # 이미지 형식
    "jpeg": [
        (b"\xFF\xD8\xFF", "JPEG"),
    ],
    "png": [
        (b"\x89PNG\r\n\x1a\n", "PNG"),
    ],
    "gif": [
        (b"GIF87a", "GIF87a"),
        (b"GIF89a", "GIF89a"),
    ],
    "bmp": [
        (b"BM", "BMP"),
    ],
    "webp": [
        (b"RIFF", "RIFF"),  # WebP는 RIFF 컨테이너 사용
    ],
    "tiff": [
        (b"\x49\x49\x2A\x00", "TIFF (Little Endian)"),
        (b"\x4D\x4D\x00\x2A", "TIFF (Big Endian)"),
    ],
    # 문서 형식
    "pdf": [
        (b"%PDF", "PDF"),
    ],
}

# 확장자별 허용되는 매직 바이트 매핑
EXTENSION_MAGIC_MAP = {
    ".jpg": ["jpeg"],
    ".jpeg": ["jpeg"],
    ".png": ["png"],
    ".gif": ["gif"],
    ".bmp": ["bmp"],
    ".webp": ["webp"],
    ".tif": ["tiff"],
    ".tiff": ["tiff"],
    ".pdf": ["pdf"],
}

# 이미지 파일로 허용되는 확장자
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}

# 모든 허용 확장자
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | {".pdf"}


def read_file_header(file_path: str | Path, size: int = 16) -> bytes:
    """파일 헤더 읽기"""
    try:
        with open(file_path, "rb") as f:
            return f.read(size)
    except Exception as e:
        logger.error(f"파일 헤더 읽기 실패: {e}")
        return b""


def read_bytes_header(content: bytes, size: int = 16) -> bytes:
    """바이트 데이터에서 헤더 읽기"""
    return content[:size] if len(content) >= size else content


def detect_file_type(header: bytes) -> Optional[str]:
    """매직 바이트로 파일 타입 감지"""
    for file_type, signatures in MAGIC_BYTES.items():
        for signature, _ in signatures:
            if header.startswith(signature):
                return file_type
    return None


def validate_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """
    파일 확장자 검증

    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return False, "파일명이 비어있습니다"

    ext = Path(filename).suffix.lower()

    if not ext:
        return False, "파일 확장자가 없습니다"

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"지원하지 않는 파일 형식입니다: {ext}. 허용: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    return True, None


def validate_magic_bytes(filename: str, content: bytes) -> Tuple[bool, Optional[str]]:
    """
    파일 매직 바이트 검증
    확장자와 실제 파일 내용이 일치하는지 확인

    Args:
        filename: 파일명 (확장자 확인용)
        content: 파일 내용 (최소 16바이트)

    Returns:
        (is_valid, error_message)
    """
    if not content:
        return False, "파일 내용이 비어있습니다"

    ext = Path(filename).suffix.lower()

    if ext not in EXTENSION_MAGIC_MAP:
        # 매직 바이트 검증이 정의되지 않은 확장자는 통과
        return True, None

    header = read_bytes_header(content)
    detected_type = detect_file_type(header)

    if detected_type is None:
        return False, f"알 수 없는 파일 형식입니다. 파일이 손상되었거나 지원하지 않는 형식입니다."

    allowed_types = EXTENSION_MAGIC_MAP[ext]

    if detected_type not in allowed_types:
        return False, f"파일 확장자({ext})와 실제 내용({detected_type})이 일치하지 않습니다"

    return True, None


def validate_file(filename: str, content: bytes) -> Tuple[bool, Optional[str]]:
    """
    파일 종합 검증 (확장자 + 매직 바이트)

    Args:
        filename: 파일명
        content: 파일 내용

    Returns:
        (is_valid, error_message)
    """
    # 1. 확장자 검증
    is_valid, error = validate_extension(filename)
    if not is_valid:
        return False, error

    # 2. 매직 바이트 검증
    is_valid, error = validate_magic_bytes(filename, content)
    if not is_valid:
        return False, error

    return True, None


def validate_image_file(filename: str, content: bytes) -> Tuple[bool, Optional[str]]:
    """
    이미지 파일 검증 (이미지 확장자만 허용)

    Args:
        filename: 파일명
        content: 파일 내용

    Returns:
        (is_valid, error_message)
    """
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"이미지 파일만 허용됩니다: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"

    return validate_file(filename, content)


def get_file_info(filename: str, content: bytes) -> dict:
    """
    파일 정보 반환

    Returns:
        {
            "filename": str,
            "extension": str,
            "size_bytes": int,
            "detected_type": str | None,
            "is_valid": bool,
            "error": str | None
        }
    """
    ext = Path(filename).suffix.lower()
    header = read_bytes_header(content)
    detected_type = detect_file_type(header)
    is_valid, error = validate_file(filename, content)

    return {
        "filename": filename,
        "extension": ext,
        "size_bytes": len(content),
        "detected_type": detected_type,
        "is_valid": is_valid,
        "error": error,
    }
