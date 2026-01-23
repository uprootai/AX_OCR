"""
eDOCr2 OCR SVG Generator

OCR 결과를 인터랙티브 SVG 오버레이로 변환
텍스트 카테고리별 색상 구분, 호버/클릭 이벤트 지원
"""

from .svg_common import escape_html, create_svg_header, create_svg_footer
from typing import List, Dict, Any, Tuple, Optional


# 텍스트 카테고리별 색상 설정
TEXT_CATEGORY_COLORS: Dict[str, str] = {
    # Dimensions
    "linear": "#FFA500",           # 오렌지 - 선형 치수
    "angular": "#FF8C00",          # 다크오렌지 - 각도 치수
    "diameter": "#FF6347",         # 토마토 - 직경
    "radius": "#FF7F50",           # 코랄 - 반경
    "text_dimension": "#FFD700",   # 골드 - 텍스트 치수 (저신뢰도)

    # GD&T
    "flatness": "#00CED1",         # 다크터콰이즈 - 평면도
    "straightness": "#20B2AA",     # 라이트씨그린 - 직진도
    "circularity": "#48D1CC",      # 미디엄터콰이즈 - 진원도
    "cylindricity": "#40E0D0",     # 터콰이즈 - 원통도
    "position": "#5F9EA0",         # 카뎃블루 - 위치도
    "concentricity": "#4682B4",    # 스틸블루 - 동심도
    "symmetry": "#6495ED",         # 콘플라워블루 - 대칭도
    "parallelism": "#7B68EE",      # 미디엄슬레이트블루 - 평행도
    "perpendicularity": "#6A5ACD", # 슬레이트블루 - 직각도
    "angularity": "#483D8B",       # 다크슬레이트블루 - 경사도
    "runout": "#8A2BE2",           # 블루바이올렛 - 흔들림
    "total_runout": "#9932CC",     # 다크오키드 - 완전흔들림
    "profile_line": "#BA55D3",     # 미디엄오키드 - 선의 윤곽도
    "profile_surface": "#DA70D6",  # 오키드 - 면의 윤곽도
    "gdt": "#00CED1",              # 다크터콰이즈 - 일반 GD&T
    "unknown": "#808080",          # 회색 - 미분류

    # Text annotations
    "text": "#9370DB",             # 미디엄퍼플 - 일반 텍스트
    "tag": "#00CED1",              # 청록 - 태그
    "note": "#9370DB",             # 보라 - 노트
    "label": "#20B2AA",            # 라이트씨그린 - 라벨
}


def generate_ocr_svg(
    dimensions: List[Dict[str, Any]],
    gdt_symbols: List[Dict[str, Any]],
    text_annotations: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    show_labels: bool = True,
    show_values: bool = True,
    interactive: bool = True,
    stroke_width: int = 2,
    opacity: float = 0.8,
) -> str:
    """
    OCR 결과를 SVG 오버레이로 변환

    Args:
        dimensions: 치수 리스트 [{value, unit, type, location, ...}]
        gdt_symbols: GD&T 심볼 리스트 [{type, value, datum, location, ...}]
        text_annotations: 텍스트 주석 리스트 [{text, location, ...}]
        image_size: (width, height) 이미지 크기
        show_labels: 라벨 표시 여부
        show_values: 값 표시 여부
        interactive: 인터랙티브 기능 활성화
        stroke_width: 테두리 두께
        opacity: 투명도

    Returns:
        SVG 문자열
    """
    width, height = image_size

    # SVG 시작
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="ocr-detection-overlay">'
    ]

    # 스타일 정의
    interactive_style = """
        .ocr-box:hover { stroke-width: 4; filter: brightness(1.2); }
        .ocr-box:hover + .ocr-label { display: block; }
        .ocr-box { cursor: pointer; }
    """ if interactive else ""

    svg_parts.append(f'''
    <defs>
        <style>
            .ocr-detection-overlay {{ pointer-events: none; }}
            .ocr-box {{
                fill: none;
                opacity: {opacity};
                pointer-events: auto;
            }}
            .ocr-box-filled {{
                opacity: 0.15;
                pointer-events: auto;
            }}
            .ocr-label {{
                font-family: 'Pretendard', Arial, sans-serif;
                font-size: 11px;
                fill: white;
                pointer-events: none;
            }}
            .ocr-label-bg {{
                opacity: 0.9;
            }}
            .ocr-value {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                fill: #333;
                font-weight: bold;
            }}
            {interactive_style}
        </style>
    </defs>
    ''')

    # 치수 레이어
    if dimensions:
        svg_parts.append('<g class="dimensions-layer">')
        for i, dim in enumerate(dimensions):
            svg_parts.append(_render_dimension(dim, i, stroke_width, show_labels, show_values))
        svg_parts.append('</g>')

    # GD&T 레이어
    if gdt_symbols:
        svg_parts.append('<g class="gdt-layer">')
        for i, gdt in enumerate(gdt_symbols):
            svg_parts.append(_render_gdt(gdt, i, stroke_width, show_labels, show_values))
        svg_parts.append('</g>')

    # 텍스트 주석 레이어
    if text_annotations:
        svg_parts.append('<g class="text-layer">')
        for i, text in enumerate(text_annotations):
            svg_parts.append(_render_text_annotation(text, i, stroke_width, show_labels))
        svg_parts.append('</g>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def _render_dimension(dim: Dict[str, Any], idx: int, stroke_width: int,
                      show_labels: bool, show_values: bool) -> str:
    """치수 렌더링"""
    location = dim.get("location", [])
    if not location:
        return ""

    # location은 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형태 또는 [x1,y1,x2,y2] 형태
    bbox = _parse_location(location)
    if not bbox:
        return ""

    x, y, w, h = bbox
    dim_type = dim.get("type", "linear")
    value = dim.get("value", "")
    unit = dim.get("unit", "mm")

    color = TEXT_CATEGORY_COLORS.get(dim_type, TEXT_CATEGORY_COLORS["linear"])

    parts = []

    # 박스 배경 (반투명)
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'class="ocr-box-filled" fill="{color}"/>'
    )

    # 박스 테두리
    escaped_value = escape_html(str(value))
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'class="ocr-box" stroke="{color}" stroke-width="{stroke_width}" '
        f'data-id="{idx}" data-type="dimension" data-category="{dim_type}" '
        f'data-value="{escaped_value}" data-unit="{unit}"/>'
    )

    # 라벨
    if show_labels or show_values:
        label_text = ""
        if show_labels:
            label_text = dim_type
        if show_values and value:
            if label_text:
                label_text += f": {value}"
            else:
                label_text = str(value)
            if unit:
                label_text += unit

        if label_text:
            label_width = len(label_text) * 6 + 8
            label_height = 16
            label_y = max(0, y - label_height - 2)

            parts.append(
                f'<rect x="{x}" y="{label_y}" width="{label_width}" height="{label_height}" '
                f'class="ocr-label-bg" fill="{color}" rx="2"/>'
            )
            parts.append(
                f'<text x="{x + 4}" y="{label_y + 12}" class="ocr-label">'
                f'{escape_html(label_text)}</text>'
            )

    return '\n'.join(parts)


def _render_gdt(gdt: Dict[str, Any], idx: int, stroke_width: int,
                show_labels: bool, show_values: bool) -> str:
    """GD&T 심볼 렌더링"""
    location = gdt.get("location", [])
    if not location:
        return ""

    bbox = _parse_location(location)
    if not bbox:
        return ""

    x, y, w, h = bbox
    gdt_type = gdt.get("type", "unknown")
    value = gdt.get("value", "")
    datum = gdt.get("datum", "")

    color = TEXT_CATEGORY_COLORS.get(gdt_type, TEXT_CATEGORY_COLORS["gdt"])

    parts = []

    # 박스 배경
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'class="ocr-box-filled" fill="{color}"/>'
    )

    # 박스 테두리 (GD&T는 점선)
    escaped_value = escape_html(str(value))
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'class="ocr-box" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-dasharray="4 2" '
        f'data-id="{idx}" data-type="gdt" data-category="{gdt_type}" '
        f'data-value="{escaped_value}" data-datum="{escape_html(str(datum))}"/>'
    )

    # 라벨
    if show_labels:
        label_text = gdt_type.replace("_", " ").title()
        if show_values and value:
            label_text += f": {value}"
        if datum:
            label_text += f" [{datum}]"

        label_width = len(label_text) * 6 + 8
        label_height = 16
        label_y = max(0, y - label_height - 2)

        parts.append(
            f'<rect x="{x}" y="{label_y}" width="{label_width}" height="{label_height}" '
            f'class="ocr-label-bg" fill="{color}" rx="2"/>'
        )
        parts.append(
            f'<text x="{x + 4}" y="{label_y + 12}" class="ocr-label">'
            f'{escape_html(label_text)}</text>'
        )

    return '\n'.join(parts)


def _render_text_annotation(text: Dict[str, Any], idx: int, stroke_width: int,
                            show_labels: bool) -> str:
    """텍스트 주석 렌더링"""
    location = text.get("location", [])
    if not location:
        return ""

    bbox = _parse_location(location)
    if not bbox:
        return ""

    x, y, w, h = bbox
    text_value = text.get("text", "")
    category = text.get("category", "text")

    color = TEXT_CATEGORY_COLORS.get(category, TEXT_CATEGORY_COLORS["text"])

    parts = []

    # 박스 배경
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'class="ocr-box-filled" fill="{color}"/>'
    )

    # 박스 테두리
    escaped_text = escape_html(str(text_value))
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'class="ocr-box" stroke="{color}" stroke-width="{stroke_width}" '
        f'data-id="{idx}" data-type="text" data-category="{category}" '
        f'data-text="{escaped_text}"/>'
    )

    # 라벨 (텍스트 값 표시)
    if show_labels and text_value:
        # 긴 텍스트는 자르기
        display_text = text_value[:30] + "..." if len(text_value) > 30 else text_value

        label_width = min(len(display_text) * 6 + 8, w + 20)
        label_height = 16
        label_y = max(0, y - label_height - 2)

        parts.append(
            f'<rect x="{x}" y="{label_y}" width="{label_width}" height="{label_height}" '
            f'class="ocr-label-bg" fill="{color}" rx="2"/>'
        )
        parts.append(
            f'<text x="{x + 4}" y="{label_y + 12}" class="ocr-label">'
            f'{escape_html(display_text)}</text>'
        )

    return '\n'.join(parts)


def _parse_location(location: Any) -> Optional[Tuple[float, float, float, float]]:
    """
    다양한 location 형식을 (x, y, width, height)로 변환

    지원 형식:
    - [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] - 4점 폴리곤
    - [x1, y1, x2, y2] - 2점 좌표
    - {"x": x, "y": y, "width": w, "height": h} - 딕셔너리
    """
    if not location:
        return None

    try:
        # 딕셔너리 형식
        if isinstance(location, dict):
            return (
                float(location.get("x", 0)),
                float(location.get("y", 0)),
                float(location.get("width", 0)),
                float(location.get("height", 0))
            )

        # 리스트 형식
        if isinstance(location, (list, tuple)):
            # 4점 폴리곤: [[x1,y1], [x2,y2], ...]
            if len(location) >= 4 and isinstance(location[0], (list, tuple)):
                xs = [p[0] for p in location]
                ys = [p[1] for p in location]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                return (x_min, y_min, x_max - x_min, y_max - y_min)

            # 2점 좌표: [x1, y1, x2, y2]
            if len(location) >= 4:
                x1, y1, x2, y2 = location[0], location[1], location[2], location[3]
                return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

            # 단일 점 + 크기: [x, y, w, h]
            if len(location) == 4:
                return tuple(float(v) for v in location)

    except (TypeError, ValueError, IndexError):
        pass

    return None


def generate_ocr_svg_minimal(
    dimensions: List[Dict[str, Any]],
    gdt_symbols: List[Dict[str, Any]],
    text_annotations: List[Dict[str, Any]],
    image_size: Tuple[int, int],
) -> str:
    """최소한의 SVG 생성 (라벨 없음, 박스만)"""
    return generate_ocr_svg(
        dimensions, gdt_symbols, text_annotations, image_size,
        show_labels=False, show_values=False, interactive=False,
        stroke_width=1, opacity=0.6
    )


def ocr_to_svg_data(
    dimensions: List[Dict[str, Any]],
    gdt_symbols: List[Dict[str, Any]],
    text_annotations: List[Dict[str, Any]],
    image_size: Tuple[int, int],
) -> Dict[str, Any]:
    """
    OCR 결과를 SVG 데이터 딕셔너리로 변환

    Args:
        dimensions: 치수 리스트
        gdt_symbols: GD&T 심볼 리스트
        text_annotations: 텍스트 주석 리스트
        image_size: (width, height)

    Returns:
        SVG 데이터 딕셔너리
    """
    return {
        "svg": generate_ocr_svg(dimensions, gdt_symbols, text_annotations, image_size),
        "svg_minimal": generate_ocr_svg_minimal(dimensions, gdt_symbols, text_annotations, image_size),
        "width": image_size[0],
        "height": image_size[1],
        "dimension_count": len(dimensions),
        "gdt_count": len(gdt_symbols),
        "text_count": len(text_annotations),
    }


