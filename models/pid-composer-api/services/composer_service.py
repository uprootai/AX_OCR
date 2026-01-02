"""
Composer Service
레이어 합성 핵심 로직
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class LayerType(str, Enum):
    """레이어 타입"""
    SYMBOLS = "symbols"
    LINES = "lines"
    TEXTS = "texts"
    REGIONS = "regions"


@dataclass
class ComposerStyle:
    """합성 스타일 설정"""
    # Symbol styles
    symbol_color: Tuple[int, int, int] = (0, 120, 255)  # Orange (BGR)
    symbol_thickness: int = 2
    symbol_fill_alpha: float = 0.1
    show_symbol_labels: bool = True
    symbol_label_size: float = 0.5

    # Line styles
    line_colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        'pipe': (0, 0, 255),      # Red
        'signal': (255, 0, 0),    # Blue
        'process': (0, 200, 0),   # Green
        'unknown': (128, 128, 128)  # Gray
    })
    line_thickness: int = 2
    show_flow_arrows: bool = False
    arrow_size: int = 10

    # Text styles
    text_color: Tuple[int, int, int] = (255, 165, 0)  # Cyan (BGR)
    text_thickness: int = 1
    show_text_values: bool = True
    text_max_length: int = 30

    # Region styles
    region_colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        'signal_group': (0, 255, 255),      # Cyan
        'equipment_boundary': (255, 0, 255), # Magenta
        'note_box': (0, 255, 0),             # Green
        'hazardous_area': (0, 0, 255),       # Red
        'unknown': (128, 128, 128)           # Gray
    })
    region_fill_alpha: float = 0.15
    region_dash_length: int = 10
    show_region_labels: bool = True


@dataclass
class ComposerResult:
    """합성 결과"""
    success: bool
    image: Optional[np.ndarray] = None
    svg: Optional[str] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def draw_symbols(
    image: np.ndarray,
    symbols: List[Dict[str, Any]],
    style: ComposerStyle
) -> np.ndarray:
    """심볼 레이어 그리기"""
    vis = image.copy()

    for symbol in symbols:
        bbox = symbol.get('bbox', {})

        # bbox 형식 처리 (dict 또는 list)
        if isinstance(bbox, dict):
            x = int(bbox.get('x', 0))
            y = int(bbox.get('y', 0))
            w = int(bbox.get('width', 0))
            h = int(bbox.get('height', 0))
        elif isinstance(bbox, list) and len(bbox) >= 4:
            x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        else:
            continue

        if w == 0 or h == 0:
            continue

        # 반투명 채우기
        if style.symbol_fill_alpha > 0:
            overlay = vis.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), style.symbol_color, -1)
            cv2.addWeighted(overlay, style.symbol_fill_alpha, vis, 1 - style.symbol_fill_alpha, 0, vis)

        # 테두리
        cv2.rectangle(vis, (x, y), (x + w, y + h), style.symbol_color, style.symbol_thickness)

        # 라벨
        if style.show_symbol_labels:
            class_name = symbol.get('class_name', symbol.get('label', 'unknown'))
            confidence = symbol.get('confidence', 0)
            label = f"{class_name}"
            if confidence > 0:
                label += f" ({confidence:.0%})"

            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, style.symbol_label_size, 1
            )

            # 라벨 배경
            cv2.rectangle(vis, (x, y - label_h - 8), (x + label_w + 4, y), style.symbol_color, -1)
            cv2.putText(vis, label, (x + 2, y - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, style.symbol_label_size, (255, 255, 255), 1)

    return vis


def draw_lines(
    image: np.ndarray,
    lines: List[Dict[str, Any]],
    style: ComposerStyle
) -> np.ndarray:
    """라인 레이어 그리기"""
    vis = image.copy()

    for line in lines:
        line_type = line.get('line_type', 'unknown')
        color = style.line_colors.get(line_type, style.line_colors.get('unknown', (128, 128, 128)))

        # 라인 스타일에 따른 대시 패턴
        line_style = line.get('line_style', 'solid')

        # Waypoints가 있으면 polyline으로 그리기
        if 'waypoints' in line and len(line['waypoints']) >= 2:
            pts = np.array([[int(p[0]), int(p[1])] for p in line['waypoints']], dtype=np.int32)

            if line_style == 'dashed':
                # 점선 그리기
                for i in range(len(pts) - 1):
                    draw_dashed_line(vis, tuple(pts[i]), tuple(pts[i+1]), color, style.line_thickness)
            else:
                cv2.polylines(vis, [pts], isClosed=False, color=color, thickness=style.line_thickness)
        else:
            start = line.get('start_point', line.get('start', [0, 0]))
            end = line.get('end_point', line.get('end', [0, 0]))
            pt1 = (int(start[0]), int(start[1]))
            pt2 = (int(end[0]), int(end[1]))

            if line_style == 'dashed':
                draw_dashed_line(vis, pt1, pt2, color, style.line_thickness)
            else:
                cv2.line(vis, pt1, pt2, color, style.line_thickness)

        # 플로우 화살표
        if style.show_flow_arrows:
            start = line.get('start_point', line.get('start', [0, 0]))
            end = line.get('end_point', line.get('end', [0, 0]))
            draw_arrow(vis, start, end, color, style.arrow_size)

    return vis


def draw_dashed_line(
    image: np.ndarray,
    pt1: Tuple[int, int],
    pt2: Tuple[int, int],
    color: Tuple[int, int, int],
    thickness: int,
    dash_length: int = 10
):
    """점선 그리기"""
    dist = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
    if dist == 0:
        return

    dashes = int(dist / (dash_length * 2))
    if dashes == 0:
        cv2.line(image, pt1, pt2, color, thickness)
        return

    for i in range(dashes + 1):
        start_ratio = (i * 2 * dash_length) / dist
        end_ratio = min(((i * 2 + 1) * dash_length) / dist, 1.0)

        if start_ratio >= 1.0:
            break

        start_x = int(pt1[0] + (pt2[0] - pt1[0]) * start_ratio)
        start_y = int(pt1[1] + (pt2[1] - pt1[1]) * start_ratio)
        end_x = int(pt1[0] + (pt2[0] - pt1[0]) * end_ratio)
        end_y = int(pt1[1] + (pt2[1] - pt1[1]) * end_ratio)

        cv2.line(image, (start_x, start_y), (end_x, end_y), color, thickness)


def draw_arrow(
    image: np.ndarray,
    start: List[float],
    end: List[float],
    color: Tuple[int, int, int],
    arrow_size: int
):
    """화살표 그리기"""
    mid_x = int((start[0] + end[0]) / 2)
    mid_y = int((start[1] + end[1]) / 2)

    # 방향 계산
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = np.sqrt(dx**2 + dy**2)

    if length > 0:
        dx, dy = dx / length, dy / length
        # 화살표 끝점
        tip_x = int(mid_x + dx * arrow_size)
        tip_y = int(mid_y + dy * arrow_size)
        cv2.arrowedLine(image, (mid_x, mid_y), (tip_x, tip_y), color, 2, tipLength=0.5)


def draw_texts(
    image: np.ndarray,
    texts: List[Dict[str, Any]],
    style: ComposerStyle
) -> np.ndarray:
    """텍스트 레이어 그리기"""
    vis = image.copy()

    for text_item in texts:
        bbox = text_item.get('bbox', [])
        position = text_item.get('position', {})

        # bbox 형식 처리
        if isinstance(bbox, list) and len(bbox) >= 4:
            if isinstance(bbox[0], list):
                # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형식
                pts = np.array(bbox, dtype=np.int32)
                cv2.polylines(vis, [pts], isClosed=True, color=style.text_color, thickness=style.text_thickness)
                x, y = int(bbox[0][0]), int(bbox[0][1])
            else:
                # [x1, y1, x2, y2] 또는 [x, y, w, h] 형식
                x1, y1 = int(bbox[0]), int(bbox[1])
                x2, y2 = int(bbox[2]), int(bbox[3])
                # x2, y2가 width, height인 경우 처리
                if x2 < x1 or y2 < y1:
                    x2, y2 = x1 + x2, y1 + y2
                cv2.rectangle(vis, (x1, y1), (x2, y2), style.text_color, style.text_thickness)
                x, y = x1, y1
        elif position:
            x = int(position.get('x', 0))
            y = int(position.get('y', 0))
            w = int(position.get('width', 0))
            h = int(position.get('height', 0))
            if w > 0 and h > 0:
                cv2.rectangle(vis, (x, y), (x + w, y + h), style.text_color, style.text_thickness)
        else:
            continue

        # 텍스트 값 표시
        if style.show_text_values:
            text_value = text_item.get('text', '')
            if text_value and len(text_value) <= style.text_max_length:
                cv2.putText(vis, text_value[:style.text_max_length], (x, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, style.text_color, 1)

    return vis


def draw_regions(
    image: np.ndarray,
    regions: List[Dict[str, Any]],
    style: ComposerStyle
) -> np.ndarray:
    """영역 레이어 그리기"""
    vis = image.copy()

    for region in regions:
        region_type = region.get('region_type', 'unknown')
        color = style.region_colors.get(region_type, style.region_colors.get('unknown', (128, 128, 128)))
        bbox = region.get('bbox', [0, 0, 0, 0])

        if len(bbox) >= 4:
            x1, y1, x2, y2 = map(int, bbox[:4])

            # x2, y2가 width, height인 경우 처리
            if x2 < x1:
                x2 = x1 + x2
            if y2 < y1:
                y2 = y1 + y2

            # 반투명 채우기
            if style.region_fill_alpha > 0:
                overlay = vis.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
                cv2.addWeighted(overlay, style.region_fill_alpha, vis, 1 - style.region_fill_alpha, 0, vis)

            # 점선 테두리
            dash = style.region_dash_length
            for start_x in range(x1, x2, dash * 2):
                end_x = min(start_x + dash, x2)
                cv2.line(vis, (start_x, y1), (end_x, y1), color, 2)
                cv2.line(vis, (start_x, y2), (end_x, y2), color, 2)
            for start_y in range(y1, y2, dash * 2):
                end_y = min(start_y + dash, y2)
                cv2.line(vis, (x1, start_y), (x1, end_y), color, 2)
                cv2.line(vis, (x2, start_y), (x2, end_y), color, 2)

            # 라벨
            if style.show_region_labels:
                label = f"#{region.get('id', '?')} {region.get('region_type_korean', region_type)}"
                cv2.putText(vis, label, (x1 + 5, y1 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return vis


def compose_layers(
    image: np.ndarray,
    layers: Dict[str, List[Dict[str, Any]]],
    enabled_layers: List[LayerType],
    style: Optional[ComposerStyle] = None
) -> ComposerResult:
    """
    레이어 합성 메인 함수

    Args:
        image: 원본 이미지 (numpy array, BGR)
        layers: 레이어 데이터 {"symbols": [...], "lines": [...], ...}
        enabled_layers: 활성화할 레이어 목록
        style: 스타일 설정

    Returns:
        ComposerResult: 합성 결과
    """
    if style is None:
        style = ComposerStyle()

    try:
        result_image = image.copy()
        stats = {
            "original_size": {"width": image.shape[1], "height": image.shape[0]},
            "layers_composed": []
        }

        # 레이어 순서: regions → lines → symbols → texts (아래에서 위로)
        layer_order = [LayerType.REGIONS, LayerType.LINES, LayerType.SYMBOLS, LayerType.TEXTS]

        for layer_type in layer_order:
            if layer_type not in enabled_layers:
                continue

            layer_data = layers.get(layer_type.value, [])
            if not layer_data:
                continue

            if layer_type == LayerType.REGIONS:
                result_image = draw_regions(result_image, layer_data, style)
            elif layer_type == LayerType.LINES:
                result_image = draw_lines(result_image, layer_data, style)
            elif layer_type == LayerType.SYMBOLS:
                result_image = draw_symbols(result_image, layer_data, style)
            elif layer_type == LayerType.TEXTS:
                result_image = draw_texts(result_image, layer_data, style)

            stats["layers_composed"].append({
                "type": layer_type.value,
                "count": len(layer_data)
            })
            logger.info(f"Composed layer: {layer_type.value} ({len(layer_data)} items)")

        stats["total_items"] = sum(lc["count"] for lc in stats["layers_composed"])

        return ComposerResult(
            success=True,
            image=result_image,
            statistics=stats
        )

    except Exception as e:
        logger.error(f"Layer composition failed: {e}")
        import traceback
        traceback.print_exc()
        return ComposerResult(success=False, error=str(e))
