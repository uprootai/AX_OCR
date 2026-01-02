"""eDOCr2 Defaults 테스트

기본 설정 패턴 테스트:
- 프로파일별 설정
- 오버라이드 적용
- 추출/전처리 설정

2026-01-02: 초기 작성
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.defaults import (
    DEFAULTS,
    get_defaults,
    get_extraction_config,
    get_preprocessing_config,
    list_profiles,
    get_profile_features,
)


class TestDefaults:
    """기본 설정 테스트"""

    def test_defaults_has_full_profile(self):
        """full 프로파일 존재"""
        assert "full" in DEFAULTS

    def test_defaults_has_dimension_only_profile(self):
        """dimension_only 프로파일 존재"""
        assert "dimension_only" in DEFAULTS

    def test_defaults_has_gdt_only_profile(self):
        """gdt_only 프로파일 존재"""
        assert "gdt_only" in DEFAULTS

    def test_defaults_has_text_only_profile(self):
        """text_only 프로파일 존재"""
        assert "text_only" in DEFAULTS

    def test_defaults_has_accurate_profile(self):
        """accurate 프로파일 존재"""
        assert "accurate" in DEFAULTS

    def test_defaults_has_fast_profile(self):
        """fast 프로파일 존재"""
        assert "fast" in DEFAULTS

    def test_defaults_has_debug_profile(self):
        """debug 프로파일 존재"""
        assert "debug" in DEFAULTS

    def test_full_profile_extracts_all(self):
        """full 프로파일은 모든 기능 활성화"""
        config = DEFAULTS["full"]
        assert config["extract_dimensions"] is True
        assert config["extract_gdt"] is True
        assert config["extract_text"] is True

    def test_dimension_only_profile(self):
        """dimension_only 프로파일은 치수만 추출"""
        config = DEFAULTS["dimension_only"]
        assert config["extract_dimensions"] is True
        assert config["extract_gdt"] is False
        assert config["extract_text"] is False

    def test_accurate_profile_uses_vl_model(self):
        """accurate 프로파일은 VL 모델 사용"""
        config = DEFAULTS["accurate"]
        assert config["use_vl_model"] is True
        assert config["use_gpu_preprocessing"] is True


class TestGetDefaults:
    """get_defaults 함수 테스트"""

    def test_get_defaults_returns_dict(self):
        """딕셔너리 반환"""
        config = get_defaults("full")
        assert isinstance(config, dict)

    def test_get_defaults_default_profile(self):
        """기본 프로파일 사용"""
        config = get_defaults()
        assert config["extract_dimensions"] is True

    def test_get_defaults_with_overrides(self):
        """오버라이드 적용"""
        config = get_defaults("full", {"visualize": True})
        assert config["visualize"] is True

    def test_get_defaults_override_none_ignored(self):
        """None 오버라이드 무시"""
        config = get_defaults("full", {"visualize": None})
        assert config["visualize"] == DEFAULTS["full"]["visualize"]

    def test_get_defaults_unknown_profile_fallback(self):
        """알 수 없는 프로파일은 기본값 사용"""
        config = get_defaults("unknown_profile")
        default_config = get_defaults("full")
        assert config["extract_dimensions"] == default_config["extract_dimensions"]


class TestGetExtractionConfig:
    """get_extraction_config 함수 테스트"""

    def test_extraction_config_has_required_keys(self):
        """필수 키 포함"""
        config = get_extraction_config("full")
        assert "extract_dimensions" in config
        assert "extract_gdt" in config
        assert "extract_text" in config

    def test_full_profile_extracts_all(self):
        """full 프로파일은 모든 추출 활성화"""
        config = get_extraction_config("full")
        assert config["extract_dimensions"] is True
        assert config["extract_gdt"] is True
        assert config["extract_text"] is True

    def test_dimension_only_extracts_dimensions(self):
        """dimension_only 프로파일은 치수만 추출"""
        config = get_extraction_config("dimension_only")
        assert config["extract_dimensions"] is True
        assert config["extract_gdt"] is False
        assert config["extract_text"] is False


class TestGetPreprocessingConfig:
    """get_preprocessing_config 함수 테스트"""

    def test_preprocessing_config_has_required_keys(self):
        """필수 키 포함"""
        config = get_preprocessing_config("full")
        assert "use_vl_model" in config
        assert "use_gpu_preprocessing" in config
        assert "visualize" in config

    def test_accurate_uses_vl_and_gpu(self):
        """accurate 프로파일은 VL/GPU 모두 사용"""
        config = get_preprocessing_config("accurate")
        assert config["use_vl_model"] is True
        assert config["use_gpu_preprocessing"] is True

    def test_fast_minimal_preprocessing(self):
        """fast 프로파일은 전처리 최소화"""
        config = get_preprocessing_config("fast")
        assert config["use_vl_model"] is False
        assert config["use_gpu_preprocessing"] is False
        assert config["visualize"] is False


class TestListProfiles:
    """list_profiles 함수 테스트"""

    def test_list_profiles_returns_dict(self):
        """딕셔너리 반환"""
        profiles = list_profiles()
        assert isinstance(profiles, dict)

    def test_list_profiles_has_all_profiles(self):
        """모든 프로파일 포함"""
        profiles = list_profiles()
        assert "full" in profiles
        assert "dimension_only" in profiles
        assert "accurate" in profiles
        assert "fast" in profiles

    def test_list_profiles_has_descriptions(self):
        """설명 포함"""
        profiles = list_profiles()
        for name, desc in profiles.items():
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestGetProfileFeatures:
    """get_profile_features 함수 테스트"""

    def test_profile_features_has_name(self):
        """이름 포함"""
        features = get_profile_features("full")
        assert "name" in features

    def test_profile_features_has_description(self):
        """설명 포함"""
        features = get_profile_features("full")
        assert "description" in features

    def test_profile_features_has_features_list(self):
        """기능 목록 포함"""
        features = get_profile_features("full")
        assert "features" in features
        assert isinstance(features["features"], list)

    def test_full_profile_has_all_features(self):
        """full 프로파일은 치수/GD&T/텍스트 추출 포함"""
        features = get_profile_features("full")
        assert "치수 추출" in features["features"]
        assert "GD&T 추출" in features["features"]
        assert "텍스트 추출" in features["features"]

    def test_accurate_profile_has_vl_feature(self):
        """accurate 프로파일은 VL 모델 사용 포함"""
        features = get_profile_features("accurate")
        assert "VL 모델 사용" in features["features"]
        assert "GPU 전처리" in features["features"]
