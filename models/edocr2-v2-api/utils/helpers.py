"""
Utility functions for eDOCr2 API
"""
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff'}


def allowed_file(filename: str) -> bool:
    """
    Validate file extension

    Args:
        filename: File name to validate

    Returns:
        True if extension is allowed
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Delete old files from directory

    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours
    """
    try:
        current_time = time.time()
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
