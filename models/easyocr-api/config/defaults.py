"""
EasyOCR 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

EasyOCR: 80+ 언어 지원, CPU 친화적
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 OCR",
        "description": "범용 텍스트 인식 (기본값)",
        "languages": "ko,en",
        "detail": True,
        "paragraph": False,
        "batch_size": 1,
        "visualize": False,
    },
    "korean": {
        "name": "한국어 OCR",
        "description": "한국어 문서 인식",
        "languages": "ko",
        "detail": True,
        "paragraph": False,
        "batch_size": 1,
        "visualize": False,
    },
    "english": {
        "name": "영어 OCR",
        "description": "영어 문서 인식",
        "languages": "en",
        "detail": True,
        "paragraph": False,
        "batch_size": 1,
        "visualize": False,
    },
    "document": {
        "name": "문서 OCR",
        "description": "문단 단위로 텍스트 그룹화",
        "languages": "ko,en",
        "detail": True,
        "paragraph": True,
        "batch_size": 1,
        "visualize": False,
    },
    "engineering": {
        "name": "도면 OCR",
        "description": "도면 텍스트/치수 인식",
        "languages": "en",
        "detail": True,
        "paragraph": False,
        "batch_size": 1,
        "visualize": False,
    },
    "fast": {
        "name": "속도 우선",
        "description": "배치 처리로 빠른 인식",
        "languages": "en",
        "detail": False,
        "paragraph": False,
        "batch_size": 4,
        "visualize": False,
    },
    "debug": {
        "name": "디버그 모드",
        "description": "시각화 포함 디버그용",
        "languages": "ko,en",
        "detail": True,
        "paragraph": False,
        "batch_size": 1,
        "visualize": True,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, korean, english, document, engineering, fast, debug)
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
        "ch_sim",  # 중국어 간체
        "ch_tra",  # 중국어 번체
        "ja",  # 일본어
        "de",  # 독일어
        "fr",  # 프랑스어
        "es",  # 스페인어
        "vi",  # 베트남어
        "th",  # 태국어
    ]


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
