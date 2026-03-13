"""
DSE Bearing Parsing — Error definitions, codes, and file validation
"""

from typing import Dict, Optional
from fastapi import UploadFile


class DSEBearingError(Exception):
    """DSE Bearing 서비스 오류"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ErrorCodes:
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    OCR_SERVICE_ERROR = "OCR_SERVICE_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    INVALID_JSON = "INVALID_JSON"
    QUOTE_GENERATION_ERROR = "QUOTE_GENERATION_ERROR"


ERROR_MESSAGES = {
    ErrorCodes.FILE_NOT_FOUND: "파일이 제공되지 않았습니다. 이미지 파일을 업로드해주세요.",
    ErrorCodes.FILE_TOO_LARGE: "파일 크기가 너무 큽니다. 최대 20MB까지 지원합니다.",
    ErrorCodes.INVALID_FILE_TYPE: "지원하지 않는 파일 형식입니다. PNG, JPG, PDF 파일만 지원합니다.",
    ErrorCodes.OCR_SERVICE_ERROR: "OCR 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
    ErrorCodes.PARSING_ERROR: "도면 파싱 중 오류가 발생했습니다.",
    ErrorCodes.CUSTOMER_NOT_FOUND: "등록되지 않은 고객입니다.",
    ErrorCodes.INVALID_JSON: "잘못된 JSON 형식입니다.",
    ErrorCodes.QUOTE_GENERATION_ERROR: "견적 생성 중 오류가 발생했습니다.",
}

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".tiff", ".tif"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def get_error_message(error_code: str, default: str = "") -> str:
    """에러 코드에 해당하는 사용자 친화적 메시지 반환"""
    return ERROR_MESSAGES.get(error_code, default or "알 수 없는 오류가 발생했습니다.")


def validate_file(file: Optional[UploadFile]) -> None:
    """파일 유효성 검사"""
    if not file or not file.filename:
        return  # 파일 선택 사항

    ext = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    if f".{ext}" not in SUPPORTED_EXTENSIONS:
        raise DSEBearingError(
            get_error_message(ErrorCodes.INVALID_FILE_TYPE),
            ErrorCodes.INVALID_FILE_TYPE,
            {"filename": file.filename, "supported": list(SUPPORTED_EXTENSIONS)}
        )
