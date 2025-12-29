"""
EasyOCR Global State Management
"""
from typing import Dict, Any

# Global cached readers
_easyocr_readers: Dict[str, Any] = {}


def get_readers() -> Dict[str, Any]:
    """Get cached EasyOCR readers dict"""
    return _easyocr_readers


def add_reader(lang_key: str, reader: Any):
    """Add reader to cache"""
    global _easyocr_readers
    _easyocr_readers[lang_key] = reader


def clear_readers():
    """Clear all cached readers"""
    global _easyocr_readers
    _easyocr_readers = {}


def has_reader(lang_key: str) -> bool:
    """Check if reader is cached"""
    return lang_key in _easyocr_readers
