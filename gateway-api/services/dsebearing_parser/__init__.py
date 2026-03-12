"""
DSE Bearing Parser Package

하위 모듈에서 모든 public 심볼을 re-export한다.
기존 `from services.dsebearing_parser import DSEBearingParser, get_parser` 유지.
"""

from .models import TitleBlockData, PartsListItem
from .constants import (
    DRAWING_NUMBER_PATTERNS,
    REVISION_PATTERNS,
    MATERIAL_PATTERNS,
    PART_NAME_KEYWORDS,
    DATE_PATTERNS,
    ISO_TOLERANCE_GRADES,
    SURFACE_ROUGHNESS,
)
from .title_block import parse_title_block
from .parts_list import parse_parts_list
from .dimensions import extract_dimensions
from .parser import DSEBearingParser

# 싱글톤 인스턴스
_parser_instance = None


def get_parser() -> DSEBearingParser:
    """파서 인스턴스 반환"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DSEBearingParser()
    return _parser_instance


__all__ = [
    # 모델
    "TitleBlockData",
    "PartsListItem",
    # 상수
    "DRAWING_NUMBER_PATTERNS",
    "REVISION_PATTERNS",
    "MATERIAL_PATTERNS",
    "PART_NAME_KEYWORDS",
    "DATE_PATTERNS",
    "ISO_TOLERANCE_GRADES",
    "SURFACE_ROUGHNESS",
    # 함수형 API
    "parse_title_block",
    "parse_parts_list",
    "extract_dimensions",
    # 클래스 API
    "DSEBearingParser",
    "get_parser",
]
