"""
PID Composer 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가

PID Composer: SVG 오버레이 시각화 생성
"""

from typing import Dict, Any, Optional


# 색상 스킴 프리셋
COLOR_SCHEMES: Dict[str, Dict[str, str]] = {
    "default": {
        "symbol": "#3b82f6",      # blue-500
        "line": "#10b981",        # emerald-500
        "text": "#f59e0b",        # amber-500
        "connection": "#8b5cf6",  # violet-500
        "highlight": "#ef4444",   # red-500
        "background": "transparent",
    },
    "dark": {
        "symbol": "#60a5fa",      # blue-400
        "line": "#34d399",        # emerald-400
        "text": "#fbbf24",        # amber-400
        "connection": "#a78bfa",  # violet-400
        "highlight": "#f87171",   # red-400
        "background": "#1f2937",  # gray-800
    },
    "print": {
        "symbol": "#1e40af",      # blue-800
        "line": "#047857",        # emerald-700
        "text": "#92400e",        # amber-800
        "connection": "#5b21b6",  # violet-800
        "highlight": "#b91c1c",   # red-700
        "background": "#ffffff",
    },
    "pid_standard": {
        "symbol": "#000000",      # black
        "line": "#0066cc",        # process line blue
        "text": "#333333",        # dark gray
        "connection": "#009933",  # instrument green
        "highlight": "#ff0000",   # red
        "background": "transparent",
    },
}


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반",
        "description": "기본 SVG 오버레이",
        "color_scheme": "default",
        "show_symbols": True,
        "show_lines": True,
        "show_texts": True,
        "show_connections": True,
        "stroke_width": 2,
        "font_size": 12,
        "opacity": 0.8,
    },
    "review": {
        "name": "도면 검토",
        "description": "도면 검토용 (모든 요소 표시)",
        "color_scheme": "default",
        "show_symbols": True,
        "show_lines": True,
        "show_texts": True,
        "show_connections": True,
        "stroke_width": 3,
        "font_size": 14,
        "opacity": 0.9,
    },
    "symbols_only": {
        "name": "심볼만",
        "description": "심볼만 표시",
        "color_scheme": "default",
        "show_symbols": True,
        "show_lines": False,
        "show_texts": False,
        "show_connections": False,
        "stroke_width": 2,
        "font_size": 12,
        "opacity": 0.8,
    },
    "connections_only": {
        "name": "연결만",
        "description": "연결 관계만 표시",
        "color_scheme": "default",
        "show_symbols": True,
        "show_lines": True,
        "show_texts": False,
        "show_connections": True,
        "stroke_width": 2,
        "font_size": 12,
        "opacity": 0.8,
    },
    "print": {
        "name": "인쇄용",
        "description": "인쇄 최적화 (고대비)",
        "color_scheme": "print",
        "show_symbols": True,
        "show_lines": True,
        "show_texts": True,
        "show_connections": True,
        "stroke_width": 1,
        "font_size": 10,
        "opacity": 1.0,
    },
    "debug": {
        "name": "디버그",
        "description": "디버그용 (모든 정보 표시)",
        "color_scheme": "default",
        "show_symbols": True,
        "show_lines": True,
        "show_texts": True,
        "show_connections": True,
        "stroke_width": 2,
        "font_size": 10,
        "opacity": 0.7,
    },
}

# 기본 프로파일
DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    프로파일에 맞는 기본 설정 반환

    Args:
        profile: 프로파일 이름
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


def get_color_scheme(scheme_name: str) -> Dict[str, str]:
    """
    색상 스킴 반환

    Args:
        scheme_name: 스킴 이름 (default, dark, print, pid_standard)

    Returns:
        색상 딕셔너리
    """
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["default"]).copy()


def list_profiles() -> Dict[str, str]:
    """
    사용 가능한 프로파일 목록과 설명 반환
    """
    return {
        profile: config.get("description", config.get("name", profile))
        for profile, config in DEFAULTS.items()
    }
