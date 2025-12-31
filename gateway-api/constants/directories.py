"""
Directory Constants - SSOT for all directory paths
모든 라우터에서 사용하는 디렉토리 경로 중앙 관리
"""

from pathlib import Path

# Base directories
GATEWAY_BASE_DIR = Path("/tmp/gateway")
UPLOAD_DIR = GATEWAY_BASE_DIR / "uploads"
RESULTS_DIR = GATEWAY_BASE_DIR / "results"


def init_directories() -> None:
    """디렉토리 초기화 (없으면 생성)"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def get_upload_dir() -> Path:
    """업로드 디렉토리 반환"""
    return UPLOAD_DIR


def get_results_dir() -> Path:
    """결과 디렉토리 반환"""
    return RESULTS_DIR


def get_project_dir(file_id: str) -> Path:
    """프로젝트별 결과 디렉토리 반환"""
    return RESULTS_DIR / file_id
