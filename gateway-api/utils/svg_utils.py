"""
공통 SVG 유틸리티

각 API의 svg_generator.py에서 사용할 공통 함수들.
이 파일은 레퍼런스 구현이며, 각 API에서 복사하여 사용합니다.

사용 예:
    from utils.svg_common import escape_html, create_svg_header, create_svg_footer
"""

from typing import Dict, Any, Optional, Tuple, List


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
    include_styles: bool = True,
    custom_styles: str = ""
) -> str:
    """SVG 헤더 생성

    Args:
        width: SVG 너비
        height: SVG 높이
        class_name: CSS 클래스명
        include_styles: 기본 스타일 포함 여부
        custom_styles: 추가 커스텀 스타일

    Returns:
        SVG 헤더 문자열
    """
    header = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="{class_name}">'
    )

    if include_styles:
        styles = f"""
<style>
.overlay-item {{
    opacity: 0.8;
    transition: all 0.2s ease;
    cursor: pointer;
}}
.overlay-item:hover {{
    stroke-width: 3;
    filter: brightness(1.2);
}}
.overlay-label {{
    font-family: 'Pretendard', 'Arial', sans-serif;
    font-size: 12px;
    fill: white;
    pointer-events: none;
}}
.overlay-label-bg {{
    opacity: 0.85;
}}
{custom_styles}
</style>
"""
        header += styles

    return header


def create_svg_footer() -> str:
    """SVG 푸터 생성"""
    return "</svg>"


def create_bbox_element(
    bbox: Dict[str, float],
    index: int,
    label: str = "",
    confidence: Optional[float] = None,
    color: str = "#3b82f6",
    stroke_width: int = 2,
    category: str = "",
    show_label: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """바운딩 박스 SVG 엘리먼트 생성

    Args:
        bbox: {'x': float, 'y': float, 'width': float, 'height': float}
        index: 인덱스 (ID 생성용)
        label: 라벨 텍스트
        confidence: 신뢰도 (0-1)
        color: 색상
        stroke_width: 선 두께
        category: 카테고리
        show_label: 라벨 표시 여부
        metadata: 추가 메타데이터 (data-* 속성으로 변환)

    Returns:
        SVG 그룹 엘리먼트
    """
    x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
    item_id = f"bbox-{index}"

    # 메타데이터를 data-* 속성으로 변환
    data_attrs = ""
    if metadata:
        data_attrs = " ".join(f'data-{k}="{escape_html(str(v))}"' for k, v in metadata.items())

    # 라벨 텍스트 생성
    label_text = label
    if confidence is not None:
        label_text += f" ({confidence * 100:.1f}%)"

    # 라벨 엘리먼트
    label_element = ""
    if show_label and label_text:
        label_width = len(label_text) * 7 + 8
        label_element = f"""
    <rect class="overlay-label-bg" x="{x}" y="{y - 20}" width="{label_width}" height="18" fill="{color}" rx="2"/>
    <text class="overlay-label" x="{x + 4}" y="{y - 6}">{escape_html(label_text)}</text>
"""

    return f"""
<g class="overlay-item overlay-bbox" id="{item_id}" data-category="{category}" {data_attrs}>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}" stroke-width="{stroke_width}"/>
    {label_element}
</g>
"""


def create_line_element(
    x1: float, y1: float, x2: float, y2: float,
    index: int,
    label: str = "",
    color: str = "#ef4444",
    stroke_width: int = 2,
    line_type: str = "solid",
    category: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """라인 SVG 엘리먼트 생성

    Args:
        x1, y1: 시작점
        x2, y2: 끝점
        index: 인덱스
        label: 라벨 텍스트
        color: 색상
        stroke_width: 선 두께
        line_type: 라인 타입 (solid, dashed, dotted, dash-dot)
        category: 카테고리
        metadata: 추가 메타데이터

    Returns:
        SVG 그룹 엘리먼트
    """
    item_id = f"line-{index}"

    # 라인 스타일
    dash_patterns = {
        "solid": "none",
        "dashed": "8,4",
        "dotted": "2,2",
        "dash-dot": "8,4,2,4"
    }
    dash_array = dash_patterns.get(line_type, "none")

    # 메타데이터
    data_attrs = ""
    if metadata:
        data_attrs = " ".join(f'data-{k}="{escape_html(str(v))}"' for k, v in metadata.items())

    # 라벨 (중간점에 표시)
    label_element = ""
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        label_width = len(label) * 7 + 8
        label_element = f"""
    <rect class="overlay-label-bg" x="{mid_x - label_width/2}" y="{mid_y - 20}" width="{label_width}" height="18" fill="{color}" rx="2"/>
    <text class="overlay-label" x="{mid_x - label_width/2 + 4}" y="{mid_y - 6}">{escape_html(label)}</text>
"""

    return f"""
<g class="overlay-item overlay-line" id="{item_id}" data-category="{category}" data-line-type="{line_type}" {data_attrs}>
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{stroke_width}" stroke-dasharray="{dash_array}"/>
    {label_element}
</g>
"""


def create_text_element(
    x: float, y: float,
    text: str,
    index: int,
    bbox: Optional[Dict[str, float]] = None,
    color: str = "#f59e0b",
    font_size: int = 12,
    category: str = "",
    show_highlight: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """텍스트 SVG 엘리먼트 생성

    Args:
        x, y: 텍스트 위치
        text: 텍스트 내용
        index: 인덱스
        bbox: 바운딩 박스 (하이라이트용)
        color: 색상
        font_size: 폰트 크기
        category: 카테고리
        show_highlight: bbox 하이라이트 표시 여부
        metadata: 추가 메타데이터

    Returns:
        SVG 그룹 엘리먼트
    """
    item_id = f"text-{index}"

    # 메타데이터
    data_attrs = ""
    if metadata:
        data_attrs = " ".join(f'data-{k}="{escape_html(str(v))}"' for k, v in metadata.items())

    # 하이라이트 박스
    highlight_element = ""
    if show_highlight and bbox:
        bx, by, bw, bh = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
        highlight_element = f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{color}" fill-opacity="0.2" stroke="{color}" stroke-width="1"/>'

    return f"""
<g class="overlay-item overlay-text" id="{item_id}" data-category="{category}" {data_attrs}>
    {highlight_element}
    <text x="{x}" y="{y}" font-size="{font_size}" fill="{color}">{escape_html(text)}</text>
</g>
"""


# 기본 색상 정의
DEFAULT_COLORS: Dict[str, str] = {
    # Detection
    "detection": "#3b82f6",  # blue
    "symbol": "#10b981",     # green

    # Lines
    "line": "#ef4444",       # red
    "pipe": "#FF0000",
    "signal": "#0000FF",
    "dashed": "#808080",
    "instrument": "#00FF00",

    # OCR
    "text": "#f59e0b",        # amber
    "dimension": "#FFA500",
    "tag": "#00CED1",
    "note": "#9370DB",

    # Region
    "region": "#8b5cf6",      # purple
}


def get_color(category: str, default: str = "#3b82f6") -> str:
    """카테고리에 해당하는 색상 반환"""
    return DEFAULT_COLORS.get(category, default)
