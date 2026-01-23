"""
공통 SVG 유틸리티

여러 API에서 공유하는 SVG 생성 함수들
"""

from typing import Dict, Any, Optional


def escape_html(text: str) -> str:
    """HTML 특수문자 이스케이프

    Args:
        text: 이스케이프할 텍스트

    Returns:
        이스케이프된 텍스트
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def create_svg_header(
    width: int,
    height: int,
    class_name: str = "detection-overlay",
) -> str:
    """SVG 헤더 생성

    Args:
        width: SVG 너비
        height: SVG 높이
        class_name: CSS 클래스명

    Returns:
        SVG 헤더 문자열
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="{class_name}">'
    )


def create_svg_footer() -> str:
    """SVG 푸터 생성"""
    return "</svg>"


def create_label_element(
    x: float,
    y: float,
    text: str,
    color: str = "#3b82f6",
    font_size: int = 12,
) -> str:
    """라벨 엘리먼트 생성 (배경 + 텍스트)

    Args:
        x, y: 위치
        text: 라벨 텍스트
        color: 배경 색상
        font_size: 폰트 크기

    Returns:
        SVG 엘리먼트 문자열
    """
    label_width = len(text) * 7 + 8
    label_height = font_size + 6
    label_y = max(0, y - label_height - 2)

    return f'''<rect x="{x}" y="{label_y}" width="{label_width}" height="{label_height}" class="detection-label-bg" fill="{color}" rx="2"/>
<text x="{x + 4}" y="{label_y + font_size + 1}" class="detection-label">{escape_html(text)}</text>'''


# 기본 색상 정의
DEFAULT_COLORS: Dict[str, str] = {
    "detection": "#3b82f6",  # blue
    "symbol": "#10b981",     # green
    "line": "#ef4444",       # red
    "text": "#f59e0b",       # amber
    "region": "#8b5cf6",     # purple
}


def get_color(category: str, default: str = "#3b82f6") -> str:
    """카테고리에 해당하는 색상 반환"""
    return DEFAULT_COLORS.get(category, default)
