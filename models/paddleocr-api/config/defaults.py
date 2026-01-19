"""
PaddleOCR 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 OCR",
        "description": "범용 텍스트 인식 (기본값)",
        "model_version": "PP-OCRv5",
        "lang": "en",
        "det_db_thresh": 0.3,
        "det_db_box_thresh": 0.6,
        "use_textline_orientation": True,
        "min_confidence": 0.5,
        "visualize": False,
    },
    "korean": {
        "name": "한국어 OCR",
        "description": "한국어 문서 인식에 최적화",
        "model_version": "PP-OCRv5",
        "lang": "korean",
        "det_db_thresh": 0.25,
        "det_db_box_thresh": 0.5,
        "use_textline_orientation": True,
        "min_confidence": 0.4,
        "visualize": False,
    },
    "engineering": {
        "name": "도면 OCR",
        "description": "기계/전기 도면 텍스트 인식",
        "model_version": "PP-OCRv5",
        "lang": "en",
        "det_db_thresh": 0.2,
        "det_db_box_thresh": 0.4,
        "use_textline_orientation": True,
        "min_confidence": 0.3,
        "visualize": False,
    },
    "accurate": {
        "name": "정확도 우선",
        "description": "높은 신뢰도 임계값으로 정확도 우선",
        "model_version": "PP-OCRv5",
        "lang": "en",
        "det_db_thresh": 0.4,
        "det_db_box_thresh": 0.7,
        "use_textline_orientation": True,
        "min_confidence": 0.7,
        "visualize": False,
    },
    "fast": {
        "name": "속도 우선",
        "description": "낮은 임계값으로 빠른 검출",
        "model_version": "PP-OCRv5",
        "lang": "en",
        "det_db_thresh": 0.2,
        "det_db_box_thresh": 0.5,
        "use_textline_orientation": False,
        "min_confidence": 0.3,
        "visualize": False,
    },
    "debug": {
        "name": "디버그 모드",
        "description": "시각화 포함 디버그용",
        "model_version": "PP-OCRv5",
        "lang": "en",
        "det_db_thresh": 0.3,
        "det_db_box_thresh": 0.6,
        "use_textline_orientation": True,
        "min_confidence": 0.5,
        "visualize": True,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, korean, engineering, accurate, fast, debug)
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


def get_detection_config(profile: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """
    검출 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        검출 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "det_db_thresh": config.get("det_db_thresh", 0.3),
        "det_db_box_thresh": config.get("det_db_box_thresh", 0.6),
        "use_textline_orientation": config.get("use_textline_orientation", True),
    }


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
