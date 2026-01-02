"""Line Detector Defaults 테스트

기본 설정 패턴 테스트:
- 프로파일별 설정
- 오버라이드 적용
- 영역/분류 설정

2026-01-02: 초기 작성
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.defaults import (
    DEFAULTS,
    DETECTION_DEFAULTS,
    get_defaults,
    get_region_config,
    get_classification_config,
    list_profiles,
    get_detection_method_info,
)


class TestDefaults:
    """기본 설정 테스트"""

    def test_defaults_has_pid_profile(self):
        """P&ID 프로파일 존재"""
        assert "pid" in DEFAULTS

    def test_defaults_has_simple_profile(self):
        """simple 프로파일 존재"""
        assert "simple" in DEFAULTS

    def test_defaults_has_region_focus_profile(self):
        """region_focus 프로파일 존재"""
        assert "region_focus" in DEFAULTS

    def test_defaults_has_connectivity_profile(self):
        """connectivity 프로파일 존재"""
        assert "connectivity" in DEFAULTS

    def test_pid_profile_enables_all_features(self):
        """P&ID 프로파일은 모든 기능 활성화"""
        config = DEFAULTS["pid"]
        assert config["classify_types"] is True
        assert config["classify_colors"] is True
        assert config["classify_styles"] is True
        assert config["find_intersections"] is True
        assert config["detect_regions"] is True

    def test_simple_profile_disables_classification(self):
        """simple 프로파일은 분류 비활성화"""
        config = DEFAULTS["simple"]
        assert config["classify_types"] is False
        assert config["classify_colors"] is False
        assert config["classify_styles"] is False
        assert config["detect_regions"] is False


class TestGetDefaults:
    """get_defaults 함수 테스트"""

    def test_get_defaults_returns_dict(self):
        """딕셔너리 반환"""
        config = get_defaults("pid")
        assert isinstance(config, dict)

    def test_get_defaults_default_profile(self):
        """기본 프로파일 사용"""
        config = get_defaults()
        assert config["method"] == "lsd"

    def test_get_defaults_with_overrides(self):
        """오버라이드 적용"""
        config = get_defaults("pid", {"min_length": 50})
        assert config["min_length"] == 50

    def test_get_defaults_override_none_ignored(self):
        """None 오버라이드 무시"""
        config = get_defaults("pid", {"min_length": None})
        assert config["min_length"] == DEFAULTS["pid"]["min_length"]

    def test_get_defaults_unknown_profile_fallback(self):
        """알 수 없는 프로파일은 기본값 사용"""
        config = get_defaults("unknown_profile")
        default_config = get_defaults("pid")
        assert config["method"] == default_config["method"]


class TestGetRegionConfig:
    """get_region_config 함수 테스트"""

    def test_region_config_has_required_keys(self):
        """필수 키 포함"""
        config = get_region_config("pid")
        assert "detect_regions" in config
        assert "region_line_styles" in config
        assert "min_region_area" in config
        assert "visualize_regions" in config

    def test_pid_profile_enables_region_detection(self):
        """P&ID 프로파일은 영역 검출 활성화"""
        config = get_region_config("pid")
        assert config["detect_regions"] is True

    def test_simple_profile_disables_region_detection(self):
        """simple 프로파일은 영역 검출 비활성화"""
        config = get_region_config("simple")
        assert config["detect_regions"] is False


class TestGetClassificationConfig:
    """get_classification_config 함수 테스트"""

    def test_classification_config_has_required_keys(self):
        """필수 키 포함"""
        config = get_classification_config("pid")
        assert "classify_types" in config
        assert "classify_colors" in config
        assert "classify_styles" in config

    def test_pid_profile_enables_all_classification(self):
        """P&ID 프로파일은 모든 분류 활성화"""
        config = get_classification_config("pid")
        assert config["classify_types"] is True
        assert config["classify_colors"] is True
        assert config["classify_styles"] is True

    def test_region_focus_only_style_classification(self):
        """region_focus는 스타일 분류만 활성화"""
        config = get_classification_config("region_focus")
        assert config["classify_types"] is False
        assert config["classify_colors"] is False
        assert config["classify_styles"] is True


class TestListProfiles:
    """list_profiles 함수 테스트"""

    def test_list_profiles_returns_dict(self):
        """딕셔너리 반환"""
        profiles = list_profiles()
        assert isinstance(profiles, dict)

    def test_list_profiles_has_all_profiles(self):
        """모든 프로파일 포함"""
        profiles = list_profiles()
        assert "pid" in profiles
        assert "simple" in profiles
        assert "region_focus" in profiles
        assert "connectivity" in profiles

    def test_list_profiles_has_descriptions(self):
        """설명 포함"""
        profiles = list_profiles()
        for name, desc in profiles.items():
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestDetectionDefaults:
    """검출 방식 기본값 테스트"""

    def test_detection_defaults_has_lsd(self):
        """LSD 방식 존재"""
        assert "lsd" in DETECTION_DEFAULTS

    def test_detection_defaults_has_hough(self):
        """Hough 방식 존재"""
        assert "hough" in DETECTION_DEFAULTS

    def test_detection_defaults_has_combined(self):
        """Combined 방식 존재"""
        assert "combined" in DETECTION_DEFAULTS

    def test_get_detection_method_info(self):
        """검출 방식 정보 반환"""
        info = get_detection_method_info("lsd")
        assert "name" in info
        assert "description" in info
        assert "merge_lines" in info

    def test_get_detection_method_info_unknown_fallback(self):
        """알 수 없는 방식은 LSD로 폴백"""
        info = get_detection_method_info("unknown")
        lsd_info = get_detection_method_info("lsd")
        assert info["name"] == lsd_info["name"]
