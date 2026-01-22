"""Table Detector Services"""

from .table_detector_service import (
    initialize_models,
    detect_tables,
    extract_table_content,
    analyze_tables
)

__all__ = [
    "initialize_models",
    "detect_tables",
    "extract_table_content",
    "analyze_tables"
]
