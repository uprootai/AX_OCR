"""
Line Detector 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가
"""

from typing import Dict, Any, Optional


# 검출 방식별 기본 설정
DETECTION_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "lsd": {
        "name": "LSD (Line Segment Detector)",
        "description": "OpenCV LSD 알고리즘 - 정밀한 직선 검출",
        "merge_lines": True,
        "min_length": 20,
        "recommended_for": ["P&ID", "기계도면"],
    },
    "hough": {
        "name": "Hough Transform",
        "description": "Hough 변환 - 노이즈에 강건",
        "merge_lines": True,
        "min_length": 30,
        "recommended_for": ["스케치", "손그림"],
    },
    "combined": {
        "name": "Combined (LSD + Hough)",
        "description": "LSD와 Hough 결합 - 최대 검출",
        "merge_lines": True,
        "min_length": 15,
        "recommended_for": ["복잡한 도면", "혼합 스타일"],
    },
}

# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "pid": {
        "name": "P&ID 라인 검출",
        "description": "P&ID 도면 배관/신호선 검출 최적화",
        "method": "lsd",
        "merge_lines": True,
        "classify_types": True,
        "classify_colors": True,
        "classify_styles": True,
        "find_intersections": True,
        "detect_regions": True,
        "region_line_styles": "dashed,dash_dot",
        "min_region_area": 5000,
        "visualize": True,
        "visualize_regions": True,
        "min_length": 20,
        "max_lines": 0,  # 제한 없음
    },
    "simple": {
        "name": "단순 라인 검출",
        "description": "라인 검출만 수행 (분류 없음)",
        "method": "lsd",
        "merge_lines": True,
        "classify_types": False,
        "classify_colors": False,
        "classify_styles": False,
        "find_intersections": False,
        "detect_regions": False,
        "region_line_styles": "",
        "min_region_area": 0,
        "visualize": True,
        "visualize_regions": False,
        "min_length": 10,
        "max_lines": 0,
    },
    "region_focus": {
        "name": "영역 검출 중심",
        "description": "점선 박스 영역 검출에 최적화",
        "method": "lsd",
        "merge_lines": True,
        "classify_types": False,
        "classify_colors": False,
        "classify_styles": True,  # 스타일 분류 필수
        "find_intersections": False,
        "detect_regions": True,
        "region_line_styles": "dashed,dash_dot,dotted",
        "min_region_area": 3000,
        "visualize": True,
        "visualize_regions": True,
        "min_length": 15,
        "max_lines": 0,
    },
    "connectivity": {
        "name": "연결성 분석",
        "description": "라인 교차점 및 연결성 분석",
        "method": "lsd",
        "merge_lines": True,
        "classify_types": True,
        "classify_colors": False,
        "classify_styles": False,
        "find_intersections": True,
        "detect_regions": False,
        "region_line_styles": "",
        "min_region_area": 0,
        "visualize": True,
        "visualize_regions": False,
        "min_length": 25,
        "max_lines": 0,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "pid"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름 (pid, simple, region_focus, connectivity)
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


def get_region_config(profile: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """
    영역 검출 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        영역 검출 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "detect_regions": config.get("detect_regions", False),
        "region_line_styles": config.get("region_line_styles", "dashed,dash_dot"),
        "min_region_area": config.get("min_region_area", 5000),
        "visualize_regions": config.get("visualize_regions", True),
    }


def get_classification_config(profile: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """
    분류 관련 설정 반환

    Args:
        profile: 프로파일 이름

    Returns:
        분류 설정 딕셔너리
    """
    config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE])

    return {
        "classify_types": config.get("classify_types", True),
        "classify_colors": config.get("classify_colors", True),
        "classify_styles": config.get("classify_styles", True),
    }


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }


def get_detection_method_info(method: str) -> Dict[str, Any]:
    """
    검출 방식 정보 반환
    """
    return DETECTION_DEFAULTS.get(method, DETECTION_DEFAULTS["lsd"]).copy()
