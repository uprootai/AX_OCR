"""
Region Module
영역 기반 텍스트 추출 및 규칙 엔진

핵심 기능:
- Line Detector 영역 + OCR 텍스트 매칭
- 유연한 규칙 기반 추출 (YAML 설정)
- UI에서 규칙 편집 가능

저자: Claude AI (Opus 4.5)
생성일: 2025-12-29
리팩토링: 2025-12-31
"""

from .models import (
    ExtractionPattern,
    RegionTextPattern,
    RegionCriteria,
    ExtractionRule,
    MatchedRegion,
)
from .rule_manager import RuleManager
from .extractor import RegionTextExtractor
from .excel_export import generate_valve_signal_excel


# =====================
# Singleton Instance
# =====================

_rule_manager_instance = None


def get_rule_manager() -> RuleManager:
    """RuleManager 싱글턴 인스턴스 반환"""
    global _rule_manager_instance
    if _rule_manager_instance is None:
        _rule_manager_instance = RuleManager()
    return _rule_manager_instance


def get_extractor() -> RegionTextExtractor:
    """RegionTextExtractor 인스턴스 반환"""
    return RegionTextExtractor(get_rule_manager())


__all__ = [
    # Models
    "ExtractionPattern",
    "RegionTextPattern",
    "RegionCriteria",
    "ExtractionRule",
    "MatchedRegion",
    # Classes
    "RuleManager",
    "RegionTextExtractor",
    # Functions
    "generate_valve_signal_excel",
    "get_rule_manager",
    "get_extractor",
]
