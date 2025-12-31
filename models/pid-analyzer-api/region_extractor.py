"""
Region Text Extractor Module
영역 기반 텍스트 추출 및 규칙 엔진

핵심 기능:
- Line Detector 영역 + OCR 텍스트 매칭
- 유연한 규칙 기반 추출 (YAML 설정)
- UI에서 규칙 편집 가능

저자: Claude AI (Opus 4.5)
생성일: 2025-12-29
리팩토링: 2025-12-31

주의: 이 파일은 하위 호환성을 위해 유지됩니다.
새 코드는 region 모듈을 직접 import하세요.

예시:
    from region import (
        RegionTextExtractor,
        RuleManager,
        get_rule_manager,
        get_extractor,
    )
"""

# 모든 클래스와 함수를 region 모듈에서 재내보내기
from region import (
    # Models
    ExtractionPattern,
    RegionTextPattern,
    RegionCriteria,
    ExtractionRule,
    MatchedRegion,
    # Classes
    RuleManager,
    RegionTextExtractor,
    # Functions
    generate_valve_signal_excel,
    get_rule_manager,
    get_extractor,
)

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
