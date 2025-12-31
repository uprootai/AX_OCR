"""
Region Module Unit Tests
영역 기반 텍스트 추출 및 규칙 엔진 테스트
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRegionModels:
    """Region 모델 테스트"""

    def test_extraction_pattern_exists(self):
        """ExtractionPattern 클래스 존재"""
        from region import ExtractionPattern

        assert ExtractionPattern is not None

    def test_region_text_pattern_exists(self):
        """RegionTextPattern 클래스 존재"""
        from region import RegionTextPattern

        assert RegionTextPattern is not None

    def test_region_criteria_exists(self):
        """RegionCriteria 클래스 존재"""
        from region import RegionCriteria

        assert RegionCriteria is not None

    def test_extraction_rule_exists(self):
        """ExtractionRule 클래스 존재"""
        from region import ExtractionRule

        assert ExtractionRule is not None

    def test_matched_region_exists(self):
        """MatchedRegion 클래스 존재"""
        from region import MatchedRegion

        assert MatchedRegion is not None


class TestRuleManager:
    """RuleManager 클래스 테스트"""

    def test_rule_manager_exists(self):
        """RuleManager 클래스 존재"""
        from region import RuleManager

        assert RuleManager is not None

    def test_get_rule_manager_singleton(self):
        """get_rule_manager 싱글턴 함수"""
        from region import get_rule_manager

        manager1 = get_rule_manager()
        manager2 = get_rule_manager()

        assert manager1 is manager2

    def test_rule_manager_instance_type(self):
        """RuleManager 인스턴스 타입"""
        from region import get_rule_manager, RuleManager

        manager = get_rule_manager()
        assert isinstance(manager, RuleManager)


class TestRegionTextExtractor:
    """RegionTextExtractor 클래스 테스트"""

    def test_extractor_exists(self):
        """RegionTextExtractor 클래스 존재"""
        from region import RegionTextExtractor

        assert RegionTextExtractor is not None

    def test_get_extractor_function(self):
        """get_extractor 함수"""
        from region import get_extractor, RegionTextExtractor

        extractor = get_extractor()
        assert isinstance(extractor, RegionTextExtractor)


class TestExcelExport:
    """Excel 내보내기 함수 테스트"""

    def test_generate_valve_signal_excel_exists(self):
        """generate_valve_signal_excel 함수 존재"""
        from region import generate_valve_signal_excel

        assert generate_valve_signal_excel is not None
        assert callable(generate_valve_signal_excel)


class TestModuleExports:
    """모듈 __all__ 내보내기 테스트"""

    def test_all_exports(self):
        """__all__ 내보내기 확인"""
        import region

        expected_exports = [
            "ExtractionPattern",
            "RegionTextPattern",
            "RegionCriteria",
            "ExtractionRule",
            "MatchedRegion",
            "RuleManager",
            "RegionTextExtractor",
            "generate_valve_signal_excel",
            "get_rule_manager",
            "get_extractor",
        ]

        for export_name in expected_exports:
            assert hasattr(region, export_name), f"Missing export: {export_name}"
