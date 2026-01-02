"""
model_defaults.py 단위 테스트
"""
import pytest
from model_defaults import (
    MODEL_DEFAULTS,
    get_model_config,
    get_sahi_config,
    list_available_models,
    DEFAULT_MODEL_TYPE
)


class TestModelDefaults:
    """MODEL_DEFAULTS 상수 테스트"""

    def test_all_models_have_required_fields(self):
        """모든 모델이 필수 필드를 가지고 있는지 확인"""
        required_fields = ["name", "confidence", "iou", "imgsz", "use_sahi"]

        for model_type, config in MODEL_DEFAULTS.items():
            for field in required_fields:
                assert field in config, f"{model_type}에 {field} 필드 없음"

    def test_confidence_range(self):
        """confidence 값이 0-1 범위인지 확인"""
        for model_type, config in MODEL_DEFAULTS.items():
            conf = config["confidence"]
            assert 0.0 <= conf <= 1.0, f"{model_type} confidence={conf} 범위 초과"

    def test_iou_range(self):
        """iou 값이 0-1 범위인지 확인"""
        for model_type, config in MODEL_DEFAULTS.items():
            iou = config["iou"]
            assert 0.0 <= iou <= 1.0, f"{model_type} iou={iou} 범위 초과"

    def test_imgsz_valid(self):
        """imgsz가 유효한 값인지 확인"""
        valid_sizes = [320, 640, 1024, 1280, 2048]

        for model_type, config in MODEL_DEFAULTS.items():
            imgsz = config["imgsz"]
            assert imgsz in valid_sizes, f"{model_type} imgsz={imgsz} 유효하지 않음"

    def test_pid_models_have_sahi_enabled(self):
        """P&ID 모델은 SAHI가 활성화되어 있어야 함"""
        pid_models = ["pid_symbol", "pid_class_aware", "pid_class_agnostic"]

        for model_type in pid_models:
            if model_type in MODEL_DEFAULTS:
                config = MODEL_DEFAULTS[model_type]
                assert config["use_sahi"] is True, f"{model_type}의 use_sahi가 False"

    def test_engineering_model_no_sahi(self):
        """engineering 모델은 SAHI가 비활성화되어 있어야 함"""
        config = MODEL_DEFAULTS.get("engineering")
        if config:
            assert config["use_sahi"] is False, "engineering의 use_sahi가 True"


class TestGetModelConfig:
    """get_model_config 함수 테스트"""

    def test_get_known_model(self):
        """알려진 모델 설정 가져오기"""
        config = get_model_config("engineering")
        assert config["name"] == "기계도면 심볼"
        assert config["confidence"] == 0.50

    def test_get_unknown_model_returns_default(self):
        """알 수 없는 모델은 기본 모델 설정 반환"""
        config = get_model_config("unknown_model_xyz")
        default_config = MODEL_DEFAULTS[DEFAULT_MODEL_TYPE]
        assert config["confidence"] == default_config["confidence"]

    def test_override_single_param(self):
        """단일 파라미터 오버라이드"""
        config = get_model_config("engineering", {"confidence": 0.8})
        assert config["confidence"] == 0.8
        assert config["iou"] == 0.45  # 원래 값 유지

    def test_override_multiple_params(self):
        """여러 파라미터 오버라이드"""
        overrides = {"confidence": 0.7, "iou": 0.6, "imgsz": 1280}
        config = get_model_config("engineering", overrides)
        assert config["confidence"] == 0.7
        assert config["iou"] == 0.6
        assert config["imgsz"] == 1280

    def test_none_override_ignored(self):
        """None 오버라이드는 무시됨"""
        config = get_model_config("engineering", {"confidence": None})
        assert config["confidence"] == 0.50  # 원래 값 유지

    def test_original_not_modified(self):
        """원본 MODEL_DEFAULTS가 수정되지 않음"""
        original_conf = MODEL_DEFAULTS["engineering"]["confidence"]
        _ = get_model_config("engineering", {"confidence": 0.99})
        assert MODEL_DEFAULTS["engineering"]["confidence"] == original_conf


class TestGetSahiConfig:
    """get_sahi_config 함수 테스트"""

    def test_pid_model_sahi_config(self):
        """P&ID 모델의 SAHI 설정"""
        config = get_sahi_config("pid_symbol")
        assert config["use_sahi"] is True
        assert config["slice_size"] == 512
        assert config["overlap_ratio"] == 0.25

    def test_engineering_model_sahi_config(self):
        """engineering 모델의 SAHI 설정"""
        config = get_sahi_config("engineering")
        assert config["use_sahi"] is False

    def test_unknown_model_returns_default(self):
        """알 수 없는 모델은 기본 SAHI 설정 반환"""
        config = get_sahi_config("unknown_model")
        default_config = MODEL_DEFAULTS[DEFAULT_MODEL_TYPE]
        assert config["use_sahi"] == default_config.get("use_sahi", False)


class TestListAvailableModels:
    """list_available_models 함수 테스트"""

    def test_returns_all_models(self):
        """모든 모델이 반환되는지 확인"""
        models = list_available_models()
        assert len(models) == len(MODEL_DEFAULTS)

    def test_returns_descriptions(self):
        """설명이 포함되는지 확인"""
        models = list_available_models()
        for model_type, description in models.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_includes_known_models(self):
        """알려진 모델이 포함되는지 확인"""
        models = list_available_models()
        expected_models = ["engineering", "pid_symbol", "bom_detector"]

        for model in expected_models:
            assert model in models, f"{model}이 목록에 없음"
