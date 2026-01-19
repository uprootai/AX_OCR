"""
Surya OCR 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

Surya OCR: 90+ 언어 지원, 레이아웃 분석 기능 포함
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 OCR",
        "description": "범용 텍스트 인식 (기본값)",
        "languages": "ko,en",
        "detect_layout": False,
        "visualize": False,
    },
    "korean": {
        "name": "한국어 OCR",
        "description": "한국어 문서 인식",
        "languages": "ko",
        "detect_layout": False,
        "visualize": False,
    },
    "english": {
        "name": "영어 OCR",
        "description": "영어 문서 인식",
        "languages": "en",
        "detect_layout": False,
        "visualize": False,
    },
    "multilingual": {
        "name": "다국어 OCR",
        "description": "한/영/중/일 다국어 인식",
        "languages": "ko,en,zh,ja",
        "detect_layout": False,
        "visualize": False,
    },
    "document": {
        "name": "문서 OCR",
        "description": "레이아웃 분석 포함 문서 인식",
        "languages": "ko,en",
        "detect_layout": True,
        "visualize": False,
    },
    "engineering": {
        "name": "도면 OCR",
        "description": "도면 텍스트/치수 인식",
        "languages": "en",
        "detect_layout": False,
        "visualize": False,
    },
    "debug": {
        "name": "디버그 모드",
        "description": "시각화 포함 디버그용",
        "languages": "ko,en",
        "detect_layout": True,
        "visualize": True,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, korean, english, multilingual, document, engineering, debug)
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


def get_supported_languages() -> list:
    """지원되는 주요 언어 코드 목록"""
    return [
        "ko",  # 한국어
        "en",  # 영어
        "zh",  # 중국어
        "ja",  # 일본어
        "de",  # 독일어
        "fr",  # 프랑스어
        "es",  # 스페인어
        "vi",  # 베트남어
        "th",  # 태국어
        "ar",  # 아랍어
    ]


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
