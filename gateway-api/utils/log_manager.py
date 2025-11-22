"""
Log Management Utility
로그 파일 관리, 로테이션, 정리, 아카이빙 기능

Features:
- Automatic log rotation based on size or time
- Old log cleanup
- Log file compression and archiving
- Log statistics and analysis
"""
import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class LogManager:
    """로그 파일 관리 클래스"""

    def __init__(self, log_dir: str = "/tmp/gateway/logs"):
        """
        Args:
            log_dir: 로그 디렉토리 경로
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_log_files(self, pattern: str = "*.log") -> List[Path]:
        """
        로그 파일 목록 조회

        Args:
            pattern: 파일 패턴 (예: "*.log", "*_error.log")

        Returns:
            로그 파일 경로 리스트
        """
        return sorted(self.log_dir.glob(pattern))

    def get_log_file_info(self, log_file: Path) -> dict:
        """
        로그 파일 정보 조회

        Args:
            log_file: 로그 파일 경로

        Returns:
            파일 정보 딕셔너리
        """
        stat = log_file.stat()
        return {
            "path": str(log_file),
            "name": log_file.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        }

    def cleanup_old_logs(self, max_age_days: int = 30, dry_run: bool = False) -> List[str]:
        """
        오래된 로그 파일 삭제

        Args:
            max_age_days: 보관 기간 (일)
            dry_run: 실제 삭제 없이 테스트만 수행

        Returns:
            삭제된 파일 경로 리스트
        """
        deleted_files = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        for log_file in self.get_log_files("*.log*"):
            file_info = self.get_log_file_info(log_file)

            if file_info["modified"] < cutoff_date:
                if not dry_run:
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file.name} (age: {file_info['age_days']} days)")
                else:
                    logger.info(f"Would delete: {log_file.name} (age: {file_info['age_days']} days)")

                deleted_files.append(str(log_file))

        return deleted_files

    def compress_logs(self, pattern: str = "*.log.[0-9]*", dry_run: bool = False) -> List[str]:
        """
        로그 파일 압축

        Args:
            pattern: 압축할 파일 패턴 (예: "*.log.[0-9]*" - 로테이션된 파일들)
            dry_run: 실제 압축 없이 테스트만 수행

        Returns:
            압축된 파일 경로 리스트
        """
        compressed_files = []

        for log_file in self.get_log_files(pattern):
            # Skip already compressed files
            if log_file.suffix == ".gz":
                continue

            compressed_path = Path(str(log_file) + ".gz")

            # Skip if compressed version exists
            if compressed_path.exists():
                continue

            if not dry_run:
                # Compress file
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Delete original
                log_file.unlink()

                original_size = log_file.stat().st_size if log_file.exists() else 0
                compressed_size = compressed_path.stat().st_size
                ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

                logger.info(
                    f"Compressed log file: {log_file.name} -> {compressed_path.name} "
                    f"(saved {ratio:.1f}%)"
                )
            else:
                logger.info(f"Would compress: {log_file.name}")

            compressed_files.append(str(compressed_path))

        return compressed_files

    def get_log_statistics(self) -> dict:
        """
        로그 파일 통계 조회

        Returns:
            통계 정보 딕셔너리
        """
        log_files = self.get_log_files("*.log*")

        total_size = sum(f.stat().st_size for f in log_files)
        total_files = len(log_files)

        # Count by type
        error_logs = len(list(self.log_dir.glob("*_error.log*")))
        general_logs = len(list(self.log_dir.glob("*.log"))) - error_logs
        compressed = len(list(self.log_dir.glob("*.gz")))

        # Age statistics
        ages = [self.get_log_file_info(f)["age_days"] for f in log_files]
        oldest_age = max(ages) if ages else 0
        newest_age = min(ages) if ages else 0

        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "general_logs": general_logs,
            "error_logs": error_logs,
            "compressed_files": compressed,
            "oldest_log_age_days": oldest_age,
            "newest_log_age_days": newest_age
        }

    def analyze_error_log(self, error_log_path: str, top_n: int = 10) -> dict:
        """
        에러 로그 분석

        Args:
            error_log_path: 에러 로그 파일 경로
            top_n: 상위 N개 에러 반환

        Returns:
            분석 결과 딕셔너리
        """
        import json
        from collections import Counter

        error_types = Counter()
        error_messages = []
        total_errors = 0

        try:
            with open(error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get("level") == "ERROR":
                            total_errors += 1

                            # Count error types
                            if "exception" in log_entry:
                                error_type = log_entry["exception"]["type"]
                                error_types[error_type] += 1

                            error_messages.append({
                                "timestamp": log_entry.get("timestamp"),
                                "message": log_entry.get("message"),
                                "module": log_entry.get("module"),
                                "function": log_entry.get("function")
                            })

                    except json.JSONDecodeError:
                        # Skip non-JSON lines
                        continue

        except FileNotFoundError:
            return {"error": f"Log file not found: {error_log_path}"}

        return {
            "total_errors": total_errors,
            "error_types": dict(error_types.most_common(top_n)),
            "recent_errors": error_messages[-top_n:] if error_messages else []
        }

    def rotate_logs_manually(self, log_file_path: str) -> bool:
        """
        수동 로그 로테이션

        Args:
            log_file_path: 로테이션할 로그 파일 경로

        Returns:
            성공 여부
        """
        log_file = Path(log_file_path)

        if not log_file.exists():
            logger.warning(f"Log file not found: {log_file_path}")
            return False

        # Generate timestamp suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_path = Path(f"{log_file_path}.{timestamp}")

        # Rename current log file
        log_file.rename(rotated_path)

        logger.info(f"Rotated log file: {log_file.name} -> {rotated_path.name}")

        # Compress rotated file
        self.compress_logs(pattern=rotated_path.name)

        return True

    def archive_logs(self, archive_dir: str, max_age_days: int = 7) -> str:
        """
        로그 파일 아카이빙

        Args:
            archive_dir: 아카이브 디렉토리 경로
            max_age_days: 아카이빙할 로그 최소 나이 (일)

        Returns:
            아카이브 파일 경로
        """
        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = archive_path / f"logs_archive_{timestamp}.tar.gz"

        import tarfile

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        archived_files = []

        with tarfile.open(archive_file, "w:gz") as tar:
            for log_file in self.get_log_files("*.log*"):
                file_info = self.get_log_file_info(log_file)

                if file_info["modified"] < cutoff_date:
                    tar.add(log_file, arcname=log_file.name)
                    archived_files.append(log_file.name)

        if archived_files:
            logger.info(f"Archived {len(archived_files)} log files to {archive_file}")

            # Delete archived files
            for log_file_name in archived_files:
                log_file = self.log_dir / log_file_name
                if log_file.exists():
                    log_file.unlink()

            return str(archive_file)
        else:
            # Delete empty archive
            archive_file.unlink()
            logger.info("No log files to archive")
            return ""


def cleanup_logs(log_dir: str = "/tmp/gateway/logs", max_age_days: int = 30, compress: bool = True):
    """
    로그 정리 편의 함수

    Args:
        log_dir: 로그 디렉토리
        max_age_days: 보관 기간 (일)
        compress: 압축 여부
    """
    manager = LogManager(log_dir)

    # Get statistics before cleanup
    stats_before = manager.get_log_statistics()
    logger.info(f"Log statistics before cleanup: {stats_before}")

    # Compress rotated logs
    if compress:
        compressed = manager.compress_logs()
        logger.info(f"Compressed {len(compressed)} log files")

    # Delete old logs
    deleted = manager.cleanup_old_logs(max_age_days=max_age_days)
    logger.info(f"Deleted {len(deleted)} old log files (older than {max_age_days} days)")

    # Get statistics after cleanup
    stats_after = manager.get_log_statistics()
    logger.info(f"Log statistics after cleanup: {stats_after}")

    saved_space = stats_before["total_size_mb"] - stats_after["total_size_mb"]
    logger.info(f"Freed up {saved_space:.2f} MB of disk space")


__all__ = [
    'LogManager',
    'cleanup_logs'
]
