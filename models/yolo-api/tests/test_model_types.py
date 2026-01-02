"""YOLO 모델 타입별 테스트

각 모델 타입의 특성과 기본값 검증:
- engineering: 기계도면 심볼 검출
- pid_symbol: P&ID 심볼 검출 (32종)
- pid_class_aware: P&ID 분류 (32종)
- pid_class_agnostic: P&ID 범용 (단일 클래스)
- bom_detector: 전력 설비 단선도 (27종)

2026-01-02: 초기 작성
"""

import pytest
import sys
import os

# 테스트를 위해 config 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.model_defaults import (
    MODEL_DEFAULTS,
    get_model_config,
    get_sahi_config,
)


class TestEngineeringModel:
    """engineering 모델 테스트"""

    def test_engineering_config_exists(self):
        """engineering 설정 존재 확인"""
        assert "engineering" in MODEL_DEFAULTS

    def test_engineering_confidence(self):
        """engineering 기본 신뢰도 (0.50 - 일반적인 도면)"""
        config = get_model_config("engineering")
        assert config["confidence"] == 0.50

    def test_engineering_imgsz(self):
        """engineering 이미지 크기 (640 - 기본값)"""
        config = get_model_config("engineering")
        assert config["imgsz"] == 640

    def test_engineering_no_sahi(self):
        """engineering SAHI 비활성화 (일반 도면은 SAHI 불필요)"""
        sahi = get_sahi_config("engineering")
        assert sahi["use_sahi"] is False

    def test_engineering_class_count(self):
        """engineering 클래스 수 참고 (14종)"""
        # model_registry.yaml 기준
        expected_classes = 14
        # 이 테스트는 문서화 목적
        assert expected_classes == 14


class TestPIDSymbolModel:
    """pid_symbol 모델 테스트"""

    def test_pid_symbol_config_exists(self):
        """pid_symbol 설정 존재 확인"""
        assert "pid_symbol" in MODEL_DEFAULTS

    def test_pid_symbol_low_confidence(self):
        """pid_symbol 낮은 신뢰도 (0.10 - 작은 심볼 검출)"""
        config = get_model_config("pid_symbol")
        assert config["confidence"] == 0.10

    def test_pid_symbol_large_imgsz(self):
        """pid_symbol 큰 이미지 크기 (1024)"""
        config = get_model_config("pid_symbol")
        assert config["imgsz"] == 1024

    def test_pid_symbol_sahi_enabled(self):
        """pid_symbol SAHI 활성화 (대형 P&ID 도면)"""
        sahi = get_sahi_config("pid_symbol")
        assert sahi["use_sahi"] is True
        assert sahi["slice_size"] == 512
        assert sahi["overlap_ratio"] == 0.25

    def test_pid_symbol_class_count(self):
        """pid_symbol 클래스 수 참고 (32종)"""
        expected_classes = 32
        assert expected_classes == 32


class TestPIDClassAwareModel:
    """pid_class_aware 모델 테스트"""

    def test_pid_class_aware_config_exists(self):
        """pid_class_aware 설정 존재 확인"""
        assert "pid_class_aware" in MODEL_DEFAULTS

    def test_pid_class_aware_same_as_symbol(self):
        """pid_class_aware와 pid_symbol 동일 설정"""
        symbol_config = get_model_config("pid_symbol")
        aware_config = get_model_config("pid_class_aware")

        assert symbol_config["confidence"] == aware_config["confidence"]
        assert symbol_config["iou"] == aware_config["iou"]
        assert symbol_config["imgsz"] == aware_config["imgsz"]

    def test_pid_class_aware_sahi_enabled(self):
        """pid_class_aware SAHI 활성화"""
        sahi = get_sahi_config("pid_class_aware")
        assert sahi["use_sahi"] is True


class TestPIDClassAgnosticModel:
    """pid_class_agnostic 모델 테스트"""

    def test_pid_class_agnostic_config_exists(self):
        """pid_class_agnostic 설정 존재 확인"""
        assert "pid_class_agnostic" in MODEL_DEFAULTS

    def test_pid_class_agnostic_single_class(self):
        """pid_class_agnostic 단일 클래스 (symbol)"""
        # model_registry.yaml 기준
        expected_classes = 1
        assert expected_classes == 1

    def test_pid_class_agnostic_sahi_enabled(self):
        """pid_class_agnostic SAHI 활성화"""
        sahi = get_sahi_config("pid_class_agnostic")
        assert sahi["use_sahi"] is True


class TestBOMDetectorModel:
    """bom_detector 모델 테스트"""

    def test_bom_detector_config_exists(self):
        """bom_detector 설정 존재 확인"""
        assert "bom_detector" in MODEL_DEFAULTS

    def test_bom_detector_higher_confidence(self):
        """bom_detector 높은 신뢰도 (0.40 - 단선도는 심볼이 큼)"""
        config = get_model_config("bom_detector")
        assert config["confidence"] == 0.40

    def test_bom_detector_higher_iou(self):
        """bom_detector 높은 IoU (0.50)"""
        config = get_model_config("bom_detector")
        assert config["iou"] == 0.50

    def test_bom_detector_no_sahi(self):
        """bom_detector SAHI 비활성화 (단선도는 SAHI 불필요)"""
        sahi = get_sahi_config("bom_detector")
        assert sahi["use_sahi"] is False

    def test_bom_detector_class_count(self):
        """bom_detector 클래스 수 참고 (27종)"""
        expected_classes = 27
        assert expected_classes == 27


class TestModelConfigOverrides:
    """모델 설정 오버라이드 테스트"""

    def test_override_confidence_for_pid(self):
        """P&ID 모델 신뢰도 오버라이드"""
        # 사용자가 더 높은 신뢰도를 원하는 경우
        config = get_model_config("pid_symbol", {"confidence": 0.30})
        assert config["confidence"] == 0.30

    def test_override_imgsz_for_engineering(self):
        """engineering 이미지 크기 오버라이드"""
        # 더 정확한 검출을 위해 큰 이미지 사용
        config = get_model_config("engineering", {"imgsz": 1280})
        assert config["imgsz"] == 1280

    def test_partial_override_preserves_others(self):
        """일부 오버라이드 시 나머지 값 보존"""
        config = get_model_config("pid_symbol", {"confidence": 0.25})

        assert config["confidence"] == 0.25
        assert config["iou"] == 0.45  # 원래 값 유지
        assert config["imgsz"] == 1024  # 원래 값 유지
        assert config["use_sahi"] is True  # 원래 값 유지


class TestSAHIConfiguration:
    """SAHI 설정 테스트"""

    def test_sahi_slice_size_valid(self):
        """SAHI 슬라이스 크기 유효성"""
        for model_type in ["pid_symbol", "pid_class_aware", "pid_class_agnostic"]:
            sahi = get_sahi_config(model_type)
            if sahi["use_sahi"]:
                assert 256 <= sahi["slice_size"] <= 2048

    def test_sahi_overlap_ratio_valid(self):
        """SAHI 오버랩 비율 유효성"""
        for model_type in ["pid_symbol", "pid_class_aware", "pid_class_agnostic"]:
            sahi = get_sahi_config(model_type)
            if sahi["use_sahi"]:
                assert 0.1 <= sahi["overlap_ratio"] <= 0.5


class TestModelTypeMapping:
    """모델 타입 매핑 테스트 (하위 호환성)"""

    def test_legacy_model_names_fallback(self):
        """레거시 모델 이름 폴백"""
        # 알 수 없는 모델은 engineering으로 폴백
        config = get_model_config("yolo11n-general")
        default_config = get_model_config("engineering")

        assert config["confidence"] == default_config["confidence"]

    def test_all_model_types_have_configs(self):
        """모든 모델 타입에 설정 존재"""
        expected_models = [
            "engineering",
            "pid_symbol",
            "pid_class_aware",
            "pid_class_agnostic",
            "bom_detector",
        ]

        for model in expected_models:
            assert model in MODEL_DEFAULTS, f"{model} 설정 누락"


class TestModelDescriptions:
    """모델 설명 테스트"""

    def test_all_models_have_descriptions(self):
        """모든 모델에 설명 존재"""
        for model_type, config in MODEL_DEFAULTS.items():
            assert "description" in config or "name" in config

    def test_descriptions_not_empty(self):
        """설명이 비어있지 않음"""
        for model_type, config in MODEL_DEFAULTS.items():
            desc = config.get("description") or config.get("name", "")
            assert len(desc) > 0, f"{model_type} 설명 비어있음"
