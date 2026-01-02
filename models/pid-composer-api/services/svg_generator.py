"""
SVG Generator Service
프론트엔드 오버레이용 SVG 생성
"""

from typing import Dict, Any, List, Tuple

from .composer_service import ComposerStyle, LayerType


def generate_svg_overlay(
    layers: Dict[str, List[Dict[str, Any]]],
    image_size: Tuple[int, int],
    enabled_layers: List[LayerType],
    style: ComposerStyle
) -> str:
    """
    SVG 오버레이 생성

    Args:
        layers: 레이어 데이터
        image_size: (width, height)
        enabled_layers: 활성화된 레이어
        style: 스타일 설정

    Returns:
        SVG 문자열
    """
    width, height = image_size

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" class="pid-composer-overlay">'
    ]

    # 스타일 정의
    symbol_rgb = f"rgb({style.symbol_color[2]},{style.symbol_color[1]},{style.symbol_color[0]})"
    text_rgb = f"rgb({style.text_color[2]},{style.text_color[1]},{style.text_color[0]})"

    svg_parts.append(f'''
    <defs>
        <style>
            .pid-composer-overlay {{ pointer-events: none; }}
            .symbol-box {{
                fill: {symbol_rgb};
                fill-opacity: {style.symbol_fill_alpha};
                stroke: {symbol_rgb};
                stroke-width: {style.symbol_thickness};
            }}
            .symbol-label {{
                font-family: Arial, sans-serif;
                font-size: {int(style.symbol_label_size * 24)}px;
                fill: {symbol_rgb};
                font-weight: bold;
            }}
            .line-pipe {{ stroke: rgb(255,0,0); stroke-width: {style.line_thickness}; fill: none; }}
            .line-signal {{ stroke: rgb(0,0,255); stroke-width: {style.line_thickness}; fill: none; }}
            .line-process {{ stroke: rgb(0,200,0); stroke-width: {style.line_thickness}; fill: none; }}
            .line-unknown {{ stroke: rgb(128,128,128); stroke-width: {style.line_thickness}; fill: none; }}
            .text-box {{ fill: none; stroke: {text_rgb}; stroke-width: {style.text_thickness}; }}
            .text-label {{ font-family: Arial, sans-serif; font-size: 10px; fill: {text_rgb}; }}
            .region-box {{
                fill: rgba(0, 255, 255, {style.region_fill_alpha});
                stroke: rgb(0,255,255);
                stroke-width: 2;
                stroke-dasharray: {style.region_dash_length},{style.region_dash_length};
            }}
            .region-label {{ font-family: Arial, sans-serif; font-size: 12px; fill: rgb(0,255,255); }}
            .interactive {{ pointer-events: auto; cursor: pointer; }}
            .interactive:hover {{ filter: brightness(1.2); }}
        </style>
    </defs>
    ''')

    # Regions 레이어 (가장 아래)
    if LayerType.REGIONS in enabled_layers:
        regions = layers.get('regions', [])
        if regions:
            svg_parts.append('<g class="regions-layer">')
            for i, region in enumerate(regions):
                bbox = region.get('bbox', [0, 0, 0, 0])
                if len(bbox) >= 4:
                    x1, y1, x2, y2 = bbox[:4]
                    # width, height 형식 처리
                    if x2 < x1:
                        x2 = x1 + x2
                    if y2 < y1:
                        y2 = y1 + y2
                    w, h = x2 - x1, y2 - y1
                    region_type = region.get('region_type', 'unknown')

                    svg_parts.append(
                        f'<rect x="{x1}" y="{y1}" width="{w}" height="{h}" '
                        f'class="region-box interactive" '
                        f'data-id="{i}" data-type="{region_type}"/>'
                    )
                    if style.show_region_labels:
                        label = region.get('region_type_korean', region_type)
                        svg_parts.append(
                            f'<text x="{x1 + 5}" y="{y1 + 15}" class="region-label">{label}</text>'
                        )
            svg_parts.append('</g>')

    # Lines 레이어
    if LayerType.LINES in enabled_layers:
        lines = layers.get('lines', [])
        if lines:
            svg_parts.append('<g class="lines-layer">')
            for i, line in enumerate(lines):
                line_type = line.get('line_type', 'unknown')
                css_class = f'line-{line_type}'
                line_style = line.get('line_style', 'solid')

                dash_attr = ''
                if line_style == 'dashed':
                    dash_attr = f'stroke-dasharray="{style.region_dash_length},{style.region_dash_length}"'

                if 'waypoints' in line and len(line['waypoints']) >= 2:
                    points = ' '.join([f"{p[0]},{p[1]}" for p in line['waypoints']])
                    svg_parts.append(
                        f'<polyline points="{points}" class="{css_class} interactive" '
                        f'{dash_attr} data-id="{i}" data-type="{line_type}"/>'
                    )
                else:
                    start = line.get('start_point', line.get('start', [0, 0]))
                    end = line.get('end_point', line.get('end', [0, 0]))
                    svg_parts.append(
                        f'<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" '
                        f'class="{css_class} interactive" {dash_attr} data-id="{i}" data-type="{line_type}"/>'
                    )

                # 플로우 화살표
                if style.show_flow_arrows:
                    start = line.get('start_point', line.get('start', [0, 0]))
                    end = line.get('end_point', line.get('end', [0, 0]))
                    mid_x = (start[0] + end[0]) / 2
                    mid_y = (start[1] + end[1]) / 2
                    svg_parts.append(
                        f'<circle cx="{mid_x}" cy="{mid_y}" r="3" fill="currentColor" class="{css_class}"/>'
                    )

            svg_parts.append('</g>')

    # Symbols 레이어
    if LayerType.SYMBOLS in enabled_layers:
        symbols = layers.get('symbols', [])
        if symbols:
            svg_parts.append('<g class="symbols-layer">')
            for i, symbol in enumerate(symbols):
                bbox = symbol.get('bbox', {})

                if isinstance(bbox, dict):
                    x = bbox.get('x', 0)
                    y = bbox.get('y', 0)
                    w = bbox.get('width', 0)
                    h = bbox.get('height', 0)
                elif isinstance(bbox, list) and len(bbox) >= 4:
                    x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                else:
                    continue

                if w == 0 or h == 0:
                    continue

                class_name = symbol.get('class_name', symbol.get('label', 'unknown'))
                confidence = symbol.get('confidence', 0)

                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                    f'class="symbol-box interactive" '
                    f'data-id="{i}" data-class="{class_name}" data-confidence="{confidence:.2f}"/>'
                )

                if style.show_symbol_labels:
                    label = f"{class_name}"
                    if confidence > 0:
                        label += f" ({confidence:.0%})"
                    svg_parts.append(
                        f'<text x="{x}" y="{y - 5}" class="symbol-label">{label}</text>'
                    )

            svg_parts.append('</g>')

    # Texts 레이어 (가장 위)
    if LayerType.TEXTS in enabled_layers:
        texts = layers.get('texts', [])
        if texts:
            svg_parts.append('<g class="texts-layer">')
            for i, text_item in enumerate(texts):
                position = text_item.get('position', {})
                bbox = text_item.get('bbox', [])

                if isinstance(bbox, list) and len(bbox) >= 4:
                    if isinstance(bbox[0], list):
                        # Polygon format
                        points = ' '.join([f"{p[0]},{p[1]}" for p in bbox])
                        svg_parts.append(
                            f'<polygon points="{points}" class="text-box interactive" '
                            f'data-id="{i}" data-text="{text_item.get("text", "")[:50]}"/>'
                        )
                    else:
                        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
                        if x2 < x1:
                            x2 = x1 + x2
                        if y2 < y1:
                            y2 = y1 + y2
                        svg_parts.append(
                            f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" '
                            f'class="text-box interactive" '
                            f'data-id="{i}" data-text="{text_item.get("text", "")[:50]}"/>'
                        )
                elif position:
                    x = position.get('x', 0)
                    y = position.get('y', 0)
                    w = position.get('width', 0)
                    h = position.get('height', 0)
                    if w > 0 and h > 0:
                        svg_parts.append(
                            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                            f'class="text-box interactive" '
                            f'data-id="{i}" data-text="{text_item.get("text", "")[:50]}"/>'
                        )

            svg_parts.append('</g>')

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)
