"""
Progress Tracking Utilities

실시간 파이프라인 진행 상황 추적
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global dictionary to store progress for each job_id
progress_store: Dict[str, List[Dict[str, Any]]] = {}


class ProgressTracker:
    """Track pipeline progress for real-time updates"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        progress_store[job_id] = []

    def update(self, step: str, status: str, message: str, data: Dict[str, Any] = None):
        """Add progress update"""
        progress_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,  # 'started', 'running', 'completed', 'error'
            "message": message,
            "data": data or {}
        }
        progress_store[self.job_id].append(progress_entry)
        logger.info(f"[{self.job_id}] {step}: {message}")

    def get_progress(self) -> List[Dict[str, Any]]:
        """Get all progress updates"""
        return progress_store.get(self.job_id, [])

    def cleanup(self):
        """Remove progress data after completion"""
        if self.job_id in progress_store:
            del progress_store[self.job_id]
