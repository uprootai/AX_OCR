"""
Line Detector SVG Generator

라인 검출 결과를 인터랙티브 SVG 오버레이로 변환
프론트엔드에서 호버, 클릭 이벤트 지원
"""

from .svg_common import escape_html, create_svg_header, create_svg_footer
from typing import List, Dict, Any, Tuple, Optional


# 라인 타입별 색상 설정
LINE_TYPE_COLORS: Dict[str, str] = {
    "pipe": "#ef4444",         # 빨강 - 배관
    "signal": "#3b82f6",       # 파랑 - 신호
    "unknown": "#10b981",      # 초록 - 미분류
}

# 라인 스타일별 색상
LINE_STYLE_COLORS: Dict[str, str] = {
    "solid": "#374151",        # 짙은 회색 - 실선
    "dashed": "#6b7280",       # 회색 - 점선
    "dashed_single_dot": "#f59e0b",  # 황색 - 일점쇄선
    "dashed_double_dot": "#8b5cf6",  # 보라 - 이점쇄선
    "dotted": "#06b6d4",       # 청록 - 점선
    "center_line": "#3b82f6",  # 파랑 - 중심선
}

# 영역 타입별 색상
REGION_TYPE_COLORS: Dict[str, str] = {
    "signal_group": "#06b6d4",       # 청록 - 신호 그룹
    "equipment_boundary": "#ec4899", # 핑크 - 장비 경계
    "note_box": "#10b981",           # 초록 - 노트 박스
    "hazardous_area": "#ef4444",     # 빨강 - 위험 구역
    "scope_boundary": "#f59e0b",     # 황색 - 스코프 경계
    "detail_area": "#eab308",        # 노랑 - 상세 영역
    "unknown": "#6b7280",            # 회색 - 미분류
}


def generate_line_svg(
    lines: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    show_labels: bool = True,
    show_intersections: bool = True,
    interactive: bool = True,
    stroke_width: int = 2,
    opacity: float = 0.8,
    color_by: str = "line_type",  # "line_type" or "line_style"
) -> str:
    """
    라인 검출 결과를 SVG 오버레이로 변환

    Args:
        lines: 라인 검출 결과 리스트 [{start_point, end_point, waypoints, line_type, ...}]
        image_size: (width, height) 이미지 크기
        show_labels: 라벨 표시 여부
        show_intersections: 교차점 표시 여부
        interactive: 인터랙티브 기능 활성화
        stroke_width: 라인 두께
        opacity: 투명도
        color_by: 색상 기준 (line_type 또는 line_style)

    Returns:
        SVG 문자열
    """
    width, height = image_size

    # SVG 시작
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="line-detection-overlay">'
    ]

    # 스타일 정의
    interactive_style = """
        .detection-line:hover { stroke-width: 4; filter: brightness(1.2); }
        .detection-line { cursor: pointer; }
        .intersection-point:hover { r: 8; }
    """ if interactive else ""

    svg_parts.append(f'''
    <defs>
        <style>
            .line-detection-overlay {{ pointer-events: none; }}
            .detection-line {{
                fill: none;
                opacity: {opacity};
                pointer-events: auto;
            }}
            .intersection-point {{
                opacity: 0.9;
                pointer-events: auto;
                cursor: pointer;
            }}
            .line-label {{
                font-family: 'Pretendard', Arial, sans-serif;
                font-size: 10px;
                fill: white;
                pointer-events: none;
            }}
            .line-label-bg {{
                opacity: 0.85;
            }}
            {interactive_style}
        </style>
    </defs>
    ''')

    # 라인 그리기
    svg_parts.append('<g class="lines-layer">')

    for i, line in enumerate(lines):
        line_type = line.get("line_type", "unknown")
        line_style = line.get("line_style", "solid")
        line_id = line.get("id", i)

        # 색상 결정
        if color_by == "line_style":
            color = LINE_STYLE_COLORS.get(line_style, "#6b7280")
        else:
            color = LINE_TYPE_COLORS.get(line_type, "#10b981")

        # waypoints가 있으면 polyline, 없으면 line
        waypoints = line.get("waypoints", [])
        if waypoints and len(waypoints) >= 2:
            points_str = " ".join([f"{p[0]},{p[1]}" for p in waypoints])
            svg_parts.append(
                f'<polyline points="{points_str}" '
                f'class="detection-line" '
                f'stroke="{color}" stroke-width="{stroke_width}" '
                f'data-id="{line_id}" data-type="{line_type}" data-style="{line_style}"/>'
            )
            # 라벨 위치 (첫 번째 점 근처)
            label_x, label_y = waypoints[0][0], waypoints[0][1] - 5
        else:
            start = line.get("start_point", [0, 0])
            end = line.get("end_point", [0, 0])
            svg_parts.append(
                f'<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" '
                f'class="detection-line" '
                f'stroke="{color}" stroke-width="{stroke_width}" '
                f'data-id="{line_id}" data-type="{line_type}" data-style="{line_style}"/>'
            )
            label_x, label_y = start[0], start[1] - 5

        # 라벨 표시
        if show_labels:
            label_text = f"#{line_id} {line_type}"
            label_width = len(label_text) * 6 + 8
            label_height = 14

            svg_parts.append(
                f'<rect x="{label_x}" y="{label_y - label_height}" '
                f'width="{label_width}" height="{label_height}" '
                f'class="line-label-bg" fill="{color}" rx="2"/>'
            )
            svg_parts.append(
                f'<text x="{label_x + 4}" y="{label_y - 3}" class="line-label">'
                f'{escape_html(label_text)}</text>'
            )

    svg_parts.append('</g>')

    # 교차점 그리기
    intersections = []
    for line in lines:
        if "intersections" in line:
            intersections.extend(line["intersections"])

    if show_intersections and intersections:
        svg_parts.append('<g class="intersections-layer">')
        for inter in intersections:
            pt = inter.get("point", [0, 0])
            inter_id = inter.get("id", "")
            svg_parts.append(
                f'<circle cx="{pt[0]}" cy="{pt[1]}" r="5" '
                f'class="intersection-point" fill="#fbbf24" stroke="#f59e0b" '
                f'data-id="{inter_id}"/>'
            )
        svg_parts.append('</g>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def generate_region_svg(
    regions: List[Dict[str, Any]],
    image_size: Tuple[int, int],
    show_labels: bool = True,
    interactive: bool = True,
    stroke_width: int = 2,
    opacity: float = 0.3,
) -> str:
    """
    영역 검출 결과를 SVG 오버레이로 변환

    Args:
        regions: 영역 검출 결과 리스트 [{bbox, region_type, ...}]
        image_size: (width, height) 이미지 크기
        show_labels: 라벨 표시 여부
        interactive: 인터랙티브 기능 활성화
        stroke_width: 테두리 두께
        opacity: 채우기 투명도

    Returns:
        SVG 문자열
    """
    width, height = image_size

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="region-detection-overlay">'
    ]

    interactive_style = """
        .region-box:hover { stroke-width: 4; filter: brightness(1.1); }
        .region-box { cursor: pointer; }
    """ if interactive else ""

    svg_parts.append(f'''
    <defs>
        <style>
            .region-detection-overlay {{ pointer-events: none; }}
            .region-box {{
                pointer-events: auto;
            }}
            .region-label {{
                font-family: 'Pretendard', Arial, sans-serif;
                font-size: 11px;
                fill: white;
                pointer-events: none;
            }}
            .region-label-bg {{
                opacity: 0.9;
            }}
            {interactive_style}
        </style>
        <!-- 점선 패턴 -->
        <pattern id="dashed-pattern" patternUnits="userSpaceOnUse" width="10" height="1">
            <line x1="0" y1="0" x2="5" y2="0" stroke="currentColor" stroke-width="2"/>
        </pattern>
    </defs>
    ''')

    svg_parts.append('<g class="regions-layer">')

    for i, region in enumerate(regions):
        bbox = region.get("bbox", [0, 0, 0, 0])
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1

        region_type = region.get("region_type", "unknown")
        region_id = region.get("id", i)
        region_korean = region.get("region_type_korean", region_type)

        color = REGION_TYPE_COLORS.get(region_type, "#6b7280")

        # 영역 박스 (점선 테두리 + 반투명 채우기)
        svg_parts.append(
            f'<rect x="{x1}" y="{y1}" width="{w}" height="{h}" '
            f'class="region-box" '
            f'fill="{color}" fill-opacity="{opacity}" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-dasharray="8 4" '
            f'data-id="{region_id}" data-type="{region_type}"/>'
        )

        # 라벨 표시
        if show_labels:
            label_text = f"#{region_id} {region_korean}"
            label_width = len(label_text) * 7 + 8
            label_height = 16

            svg_parts.append(
                f'<rect x="{x1}" y="{y1 - label_height - 2}" '
                f'width="{label_width}" height="{label_height}" '
                f'class="region-label-bg" fill="{color}" rx="2"/>'
            )
            svg_parts.append(
                f'<text x="{x1 + 4}" y="{y1 - 5}" class="region-label">'
                f'{escape_html(label_text)}</text>'
            )

    svg_parts.append('</g>')
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def lines_to_svg_data(
    lines: List[Dict[str, Any]],
    image_size: Tuple[int, int],
) -> Dict[str, Any]:
    """
    라인 검출 결과를 SVG 데이터 딕셔너리로 변환

    Args:
        lines: 라인 검출 결과 리스트
        image_size: (width, height)

    Returns:
        SVG 데이터 딕셔너리
    """
    return {
        "svg": generate_line_svg(lines, image_size),
        "svg_minimal": generate_line_svg(
            lines, image_size,
            show_labels=False, show_intersections=False, interactive=False
        ),
        "width": image_size[0],
        "height": image_size[1],
        "line_count": len(lines),
    }


def regions_to_svg_data(
    regions: List[Dict[str, Any]],
    image_size: Tuple[int, int],
) -> Dict[str, Any]:
    """
    영역 검출 결과를 SVG 데이터 딕셔너리로 변환

    Args:
        regions: 영역 검출 결과 리스트
        image_size: (width, height)

    Returns:
        SVG 데이터 딕셔너리
    """
    return {
        "svg": generate_region_svg(regions, image_size),
        "svg_minimal": generate_region_svg(
            regions, image_size,
            show_labels=False, interactive=False
        ),
        "width": image_size[0],
        "height": image_size[1],
        "region_count": len(regions),
    }


