"""
Region Detection Service
영역 검출 관련 함수
"""

import logging
from typing import List, Dict, Tuple

import cv2
import numpy as np

from .constants import REGION_TYPES

logger = logging.getLogger(__name__)


def find_dashed_regions(image: np.ndarray, lines: List[Dict],
                        min_area: int = 5000,
                        line_styles: List[str] = None,
                        aspect_ratio_range: Tuple[float, float] = (0.2, 5.0)) -> List[Dict]:
    """
    점선/특정 스타일 라인으로 둘러싸인 영역(박스) 찾기
    """
    if line_styles is None:
        line_styles = ['dashed', 'dash_dot']

    h, w = image.shape[:2]

    # 특정 스타일 라인만 필터링
    filtered_lines = [l for l in lines if l.get('line_style', 'unknown') in line_styles]

    if len(filtered_lines) < 4:
        return []

    logger.info(f"Region detection: {len(filtered_lines)} {line_styles} lines found")

    # 라인을 이진 마스크로 변환
    mask = np.zeros((h, w), dtype=np.uint8)

    for line in filtered_lines:
        if 'waypoints' in line and len(line['waypoints']) >= 2:
            pts = np.array([[int(p[0]), int(p[1])] for p in line['waypoints']], dtype=np.int32)
            cv2.polylines(mask, [pts], isClosed=False, color=255, thickness=3)
        else:
            pt1 = (int(line['start_point'][0]), int(line['start_point'][1]))
            pt2 = (int(line['end_point'][0]), int(line['end_point'][1]))
            cv2.line(mask, pt1, pt2, 255, 3)

    # 형태학적 연산으로 갭 연결
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)

    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_dilated = cv2.dilate(mask_closed, kernel_dilate, iterations=2)

    # 윤곽선 검출
    contours, hierarchy = cv2.findContours(mask_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    region_id = 0

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        if area < min_area:
            continue

        # 사각형 근사화
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        x, y, box_w, box_h = cv2.boundingRect(contour)

        aspect_ratio = box_w / box_h if box_h > 0 else 0
        if not (aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]):
            continue

        rect = cv2.minAreaRect(contour)
        box_points = cv2.boxPoints(rect)
        box_points = box_points.astype(np.intp)

        lines_inside = count_lines_in_region(lines, (x, y, x + box_w, y + box_h))

        region = {
            'id': region_id,
            'bbox': [int(x), int(y), int(x + box_w), int(y + box_h)],
            'center': [int(x + box_w / 2), int(y + box_h / 2)],
            'area': int(area),
            'width': int(box_w),
            'height': int(box_h),
            'aspect_ratio': round(aspect_ratio, 2),
            'vertices': len(approx),
            'is_rectangular': len(approx) == 4,
            'rotated_box': box_points.tolist(),
            'rotation_angle': round(rect[2], 1),
            'enclosing_line_style': line_styles[0] if len(line_styles) == 1 else 'mixed',
            'lines_inside_count': lines_inside,
            'region_type': 'unknown',
            'region_type_korean': '미분류',
            'confidence': 0.0
        }

        regions.append(region)
        region_id += 1

    logger.info(f"Found {len(regions)} closed regions")
    return regions


def count_lines_in_region(lines: List[Dict], bbox: Tuple[int, int, int, int]) -> int:
    """
    특정 영역 내부에 있는 라인 수 카운트
    """
    x1, y1, x2, y2 = bbox
    count = 0

    for line in lines:
        start = line['start_point']
        end = line['end_point']
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2

        if x1 <= mid_x <= x2 and y1 <= mid_y <= y2:
            count += 1

    return count


def get_symbols_in_region(symbols: List[Dict], region: Dict,
                          margin: int = 10) -> List[Dict]:
    """
    특정 영역 내에 있는 심볼 필터링
    """
    x1, y1, x2, y2 = region['bbox']
    x1 -= margin
    y1 -= margin
    x2 += margin
    y2 += margin

    symbols_inside = []

    for symbol in symbols:
        if 'center' in symbol:
            cx, cy = symbol['center']
        elif 'bbox' in symbol:
            sx1, sy1, sx2, sy2 = symbol['bbox']
            cx, cy = (sx1 + sx2) / 2, (sy1 + sy2) / 2
        else:
            continue

        if x1 <= cx <= x2 and y1 <= cy <= y2:
            symbols_inside.append(symbol)

    return symbols_inside


def classify_region_type_by_keywords(text: str) -> Tuple[str, float]:
    """
    텍스트 키워드로 영역 타입 분류
    """
    text_upper = text.upper()

    for region_type, info in REGION_TYPES.items():
        if region_type == 'unknown':
            continue

        for keyword in info['keywords']:
            if keyword in text_upper:
                return region_type, 0.85

    return 'unknown', 0.3
