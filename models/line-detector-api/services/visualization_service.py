"""
Visualization Service
시각화 관련 함수
"""

import base64
from typing import List, Dict

import cv2
import numpy as np


def visualize_lines(image: np.ndarray, lines: List[Dict],
                    intersections: List[Dict] = None) -> np.ndarray:
    """
    라인 검출 결과 시각화 - waypoints가 있으면 polyline으로 그림
    """
    vis = image.copy()

    colors = {
        'pipe': (0, 0, 255),      # Red
        'signal': (255, 0, 0),    # Blue
        'unknown': (0, 255, 0)    # Green
    }

    for line in lines:
        line_type = line.get('line_type', 'unknown')
        color = colors.get(line_type, (0, 255, 0))

        if 'waypoints' in line and len(line['waypoints']) >= 2:
            pts = np.array([[int(p[0]), int(p[1])] for p in line['waypoints']], dtype=np.int32)
            cv2.polylines(vis, [pts], isClosed=False, color=color, thickness=2)
        else:
            pt1 = (int(line['start_point'][0]), int(line['start_point'][1]))
            pt2 = (int(line['end_point'][0]), int(line['end_point'][1]))
            cv2.line(vis, pt1, pt2, color, 2)

    if intersections:
        for inter in intersections:
            pt = (int(inter['point'][0]), int(inter['point'][1]))
            cv2.circle(vis, pt, 5, (255, 255, 0), -1)  # Yellow

    return vis


def visualize_regions(image: np.ndarray, regions: List[Dict],
                      draw_labels: bool = True) -> np.ndarray:
    """
    검출된 영역 시각화
    """
    vis = image.copy()

    type_colors = {
        'signal_group': (0, 255, 255),      # Cyan
        'equipment_boundary': (255, 0, 255), # Magenta
        'note_box': (0, 255, 0),             # Green
        'hazardous_area': (0, 0, 255),       # Red
        'scope_boundary': (255, 165, 0),     # Orange
        'detail_area': (255, 255, 0),        # Yellow
        'unknown': (128, 128, 128),          # Gray
    }

    for region in regions:
        region_type = region.get('region_type', 'unknown')
        color = type_colors.get(region_type, (128, 128, 128))

        x1, y1, x2, y2 = region['bbox']

        # 영역 테두리 (점선 효과)
        dash_length = 10
        for start_x in range(x1, x2, dash_length * 2):
            end_x = min(start_x + dash_length, x2)
            cv2.line(vis, (start_x, y1), (end_x, y1), color, 2)
            cv2.line(vis, (start_x, y2), (end_x, y2), color, 2)
        for start_y in range(y1, y2, dash_length * 2):
            end_y = min(start_y + dash_length, y2)
            cv2.line(vis, (x1, start_y), (x1, end_y), color, 2)
            cv2.line(vis, (x2, start_y), (x2, end_y), color, 2)

        # 영역 내부 반투명 채우기
        overlay = vis.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, 0.1, vis, 0.9, 0, vis)

        # 라벨 표시
        if draw_labels:
            label = f"#{region['id']} {region.get('region_type_korean', '영역')}"
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(vis, (x1, y1 - text_h - 8), (x1 + text_w + 4, y1), color, -1)
            cv2.putText(vis, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return vis


def numpy_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 변환"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')
