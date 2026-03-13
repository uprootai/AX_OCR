"""
Result Manager - 공통 상수 및 환경 변수
"""
import os

# 기본 결과 저장 디렉토리
DEFAULT_RESULT_DIR = os.getenv("RESULT_SAVE_DIR", "/tmp/gateway/results")

# 기본 보관 기간 (일)
DEFAULT_RETENTION_DAYS = int(os.getenv("RESULT_RETENTION_DAYS", "7"))

# 업로드 파일 디렉토리
DEFAULT_UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/gateway/uploads")

# 업로드 파일 보관 기간 (시간)
DEFAULT_UPLOAD_TTL_HOURS = int(os.getenv("UPLOAD_TTL_HOURS", "24"))

# 정리 스케줄 설정
CLEANUP_INTERVAL_HOURS = int(os.getenv("RESULT_CLEANUP_INTERVAL_HOURS", "24"))
CLEANUP_HOUR = int(os.getenv("RESULT_CLEANUP_HOUR", "2"))
