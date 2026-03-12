"""
Upload Cleanup Unit Tests
업로드 파일 자동 삭제 및 접근 로그 테스트
"""
import os
import time
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch


class TestUploadCleanup:
    """업로드 파일 TTL 삭제 테스트"""

    def test_cleanup_empty_directory(self, tmp_path):
        """빈 디렉토리에서 정리"""
        from utils.result_manager import ResultManager

        manager = ResultManager(base_dir=str(tmp_path / "results"))
        result = manager.cleanup_old_uploads(
            upload_dir=str(tmp_path / "uploads"),
            max_age_hours=24
        )
        assert result["deleted_count"] == 0

    def test_cleanup_old_files(self, tmp_path):
        """TTL 초과 파일 삭제"""
        from utils.result_manager import ResultManager

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()

        # Create old file (modify time to 25 hours ago)
        old_file = upload_dir / "old_drawing.png"
        old_file.write_bytes(b"fake image data" * 100)
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        new_file = upload_dir / "new_drawing.png"
        new_file.write_bytes(b"recent image data")

        manager = ResultManager(base_dir=str(tmp_path / "results"))
        result = manager.cleanup_old_uploads(
            upload_dir=str(upload_dir),
            max_age_hours=24
        )

        assert result["deleted_count"] == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_cleanup_dry_run(self, tmp_path):
        """dry_run 모드에서는 삭제하지 않음"""
        from utils.result_manager import ResultManager

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()

        old_file = upload_dir / "old_drawing.png"
        old_file.write_bytes(b"fake data")
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))

        manager = ResultManager(base_dir=str(tmp_path / "results"))
        result = manager.cleanup_old_uploads(
            upload_dir=str(upload_dir),
            max_age_hours=24,
            dry_run=True
        )

        assert result["deleted_count"] == 1
        assert result["dry_run"] is True
        assert old_file.exists()  # Not actually deleted


class TestUploadLogging:
    """업로드 이벤트 로깅 테스트"""

    def test_log_upload_event(self):
        """업로드 로그 이벤트 생성"""
        from utils.logging_middleware import log_upload_event

        # Should not raise
        log_upload_event("test.png", 1024, ttl_hours=24)

    def test_log_upload_event_default_ttl(self):
        """기본 TTL 값 확인"""
        from utils.logging_middleware import log_upload_event

        # Should not raise with default ttl
        log_upload_event("blueprint.pdf", 5_000_000)
