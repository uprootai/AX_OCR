"""
Utility functions for EDGNet API
"""
import time
import logging
from pathlib import Path
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Validate file extension

    Args:
        filename: File name to check
        allowed_extensions: Set of allowed extensions

    Returns:
        True if file extension is allowed
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def bezier_to_bbox(bezier_curve, n_samples: int = 50) -> Dict[str, int]:
    """
    Convert Bezier curve to bounding box

    Args:
        bezier_curve: Bezier curve object with evaluate() method
        n_samples: Number of points to sample for bbox calculation

    Returns:
        Bounding box dict: {'x': int, 'y': int, 'width': int, 'height': int}
    """
    try:
        t_vals = np.linspace(0, 1, n_samples)
        points = bezier_curve.evaluate(t_vals)

        x_min = int(np.min(points[:, 0]))
        y_min = int(np.min(points[:, 1]))
        x_max = int(np.max(points[:, 0]))
        y_max = int(np.max(points[:, 1]))

        return {
            'x': x_min,
            'y': y_min,
            'width': x_max - x_min,
            'height': y_max - y_min
        }
    except Exception as e:
        logger.error(f"Failed to compute bbox: {e}")
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0}


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Clean up old files from directory

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
