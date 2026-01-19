"""
DocTR 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

DocTR: 2단계 파이프라인 (Detection + Recognition)
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반 OCR",
        "description": "범용 텍스트 인식 (기본값)",
        "straighten_pages": False,
        "export_as_xml": False,
        "visualize": False,
    },
    "document": {
        "name": "문서 OCR",
        "description": "페이지 정렬 포함 문서 인식",
        "straighten_pages": True,
        "export_as_xml": False,
        "visualize": False,
    },
    "structured": {
        "name": "구조화 OCR",
        "description": "XML 출력으로 구조 보존",
        "straighten_pages": True,
        "export_as_xml": True,
        "visualize": False,
    },
    "engineering": {
        "name": "도면 OCR",
        "description": "도면 텍스트/치수 인식",
        "straighten_pages": False,
        "export_as_xml": False,
        "visualize": False,
    },
    "scanned": {
        "name": "스캔 문서",
        "description": "스캔 문서 인식 (페이지 정렬)",
        "straighten_pages": True,
        "export_as_xml": False,
        "visualize": False,
    },
    "debug": {
        "name": "디버그 모드",
        "description": "시각화 포함 디버그용",
        "straighten_pages": False,
        "export_as_xml": False,
        "visualize": True,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (general, document, structured, engineering, scanned, debug)
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


def get_output_config(profile: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """
    출력 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        출력 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "export_as_xml": config.get("export_as_xml", False),
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
