"""
Result Manager - 싱글톤 인스턴스 및 헬퍼 함수
"""
from typing import Optional

from .constants import DEFAULT_RETENTION_DAYS
from .core import ResultManager

_result_manager: Optional[ResultManager] = None


def get_result_manager() -> ResultManager:
    """ResultManager 싱글톤 인스턴스 반환"""
    global _result_manager
    if _result_manager is None:
        _result_manager = ResultManager()
    return _result_manager


def cleanup_results(max_age_days: int = DEFAULT_RETENTION_DAYS, dry_run: bool = False):
    """
    결과 정리 헬퍼 함수

    사용 예:
        from utils.result_manager import cleanup_results
        cleanup_results(max_age_days=7)
    """
    manager = get_result_manager()
    return manager.cleanup_old_results(max_age_days=max_age_days, dry_run=dry_run)
