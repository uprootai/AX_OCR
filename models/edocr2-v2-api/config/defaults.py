"""
eDOCr2 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "full": {
        "name": "전체 추출",
        "description": "치수, GD&T, 텍스트 모두 추출",
        "extract_dimensions": True,
        "extract_gdt": True,
        "extract_text": True,
        "use_vl_model": False,
        "visualize": False,
        "use_gpu_preprocessing": False,
    },
    "dimension_only": {
        "name": "치수만 추출",
        "description": "치수 정보만 빠르게 추출",
        "extract_dimensions": True,
        "extract_gdt": False,
        "extract_text": False,
        "use_vl_model": False,
        "visualize": False,
        "use_gpu_preprocessing": False,
    },
    "gdt_only": {
        "name": "GD&T만 추출",
        "description": "기하공차/데이텀만 추출",
        "extract_dimensions": False,
        "extract_gdt": True,
        "extract_text": False,
        "use_vl_model": False,
        "visualize": False,
        "use_gpu_preprocessing": False,
    },
    "text_only": {
        "name": "텍스트만 추출",
        "description": "일반 텍스트만 추출",
        "extract_dimensions": False,
        "extract_gdt": False,
        "extract_text": True,
        "use_vl_model": False,
        "visualize": False,
        "use_gpu_preprocessing": False,
    },
    "accurate": {
        "name": "정확도 우선",
        "description": "VL 모델 사용 + GPU 전처리로 최대 정확도",
        "extract_dimensions": True,
        "extract_gdt": True,
        "extract_text": True,
        "use_vl_model": True,
        "visualize": True,
        "use_gpu_preprocessing": True,
    },
    "fast": {
        "name": "속도 우선",
        "description": "치수만 빠르게 추출 (VL 모델 미사용)",
        "extract_dimensions": True,
        "extract_gdt": False,
        "extract_text": False,
        "use_vl_model": False,
        "visualize": False,
        "use_gpu_preprocessing": False,
    },
    "debug": {
        "name": "디버그 모드",
        "description": "모든 기능 + 시각화 활성화",
        "extract_dimensions": True,
        "extract_gdt": True,
        "extract_text": True,
        "use_vl_model": False,
        "visualize": True,
        "use_gpu_preprocessing": False,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "full"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (full, dimension_only, gdt_only, text_only, accurate, fast, debug)
        overrides: 덮어쓸 파라미터

    Returns:
        설정 딕셔너리
    """
    base_config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE]).copy()

    if overrides:
        for key, value in overrides.items():
            if value is not None:
                base_config[key] = value

    return base_config


def get_extraction_config(profile: str = DEFAULT_PROFILE) -> Dict[str, bool]:
    """
    추출 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        추출 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "extract_dimensions": config.get("extract_dimensions", True),
        "extract_gdt": config.get("extract_gdt", True),
        "extract_text": config.get("extract_text", True),
    }


def get_preprocessing_config(profile: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """
    전처리 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        전처리 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "use_vl_model": config.get("use_vl_model", False),
        "use_gpu_preprocessing": config.get("use_gpu_preprocessing", False),
        "visualize": config.get("visualize", False),
    }


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }


def get_profile_features(profile: str) -> Dict[str, Any]:
    """
    프로파일의 주요 특성 반환 (API 문서화용)
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    features = []
    if config.get("extract_dimensions"):
        features.append("치수 추출")
    if config.get("extract_gdt"):
        features.append("GD&T 추출")
    if config.get("extract_text"):
        features.append("텍스트 추출")
    if config.get("use_vl_model"):
        features.append("VL 모델 사용")
    if config.get("use_gpu_preprocessing"):
        features.append("GPU 전처리")
    if config.get("visualize"):
        features.append("시각화")

    return {
        "name": config.get("name", profile),
        "description": config.get("description", ""),
        "features": features,
    }
