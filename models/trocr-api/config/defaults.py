"""
TrOCR 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

Model Types:
  - printed: 인쇄체 텍스트 인식 (기본)
  - handwritten: 필기체 텍스트 인식
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 OCR",
        "description": "범용 텍스트 인식 (기본값)",
        "model_type": "printed",
        "max_length": 64,
        "num_beams": 4,
    },
    "printed": {
        "name": "인쇄체 OCR",
        "description": "인쇄된 텍스트 인식에 최적화",
        "model_type": "printed",
        "max_length": 64,
        "num_beams": 4,
    },
    "handwritten": {
        "name": "필기체 OCR",
        "description": "손글씨 텍스트 인식",
        "model_type": "handwritten",
        "max_length": 64,
        "num_beams": 4,
    },
    "engineering": {
        "name": "도면 OCR",
        "description": "도면 텍스트/치수 인식",
        "model_type": "printed",
        "max_length": 32,
        "num_beams": 3,
    },
    "accurate": {
        "name": "정확도 우선",
        "description": "더 많은 빔 탐색으로 정확도 향상",
        "model_type": "printed",
        "max_length": 128,
        "num_beams": 8,
    },
    "fast": {
        "name": "속도 우선",
        "description": "그리디 디코딩으로 빠른 인식",
        "model_type": "printed",
        "max_length": 32,
        "num_beams": 1,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, printed, handwritten, engineering, accurate, fast)
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


def get_decoding_config(profile: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """
    디코딩 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        디코딩 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "max_length": config.get("max_length", 64),
        "num_beams": config.get("num_beams", 4),
    }


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
