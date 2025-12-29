"""
Line Classification Service
라인 유형/색상/스타일 분류 함수
"""

import logging
from typing import List, Dict

import cv2
import numpy as np

from .constants import LINE_COLOR_TYPES, LINE_STYLE_TYPES, LINE_PURPOSE_TYPES

logger = logging.getLogger(__name__)


def classify_line_type(line: Dict, all_lines: List[Dict]) -> str:
    """
    라인 유형 분류 (배관 vs 신호선)

    규칙 기반 분류:
    - 굵은 실선 → 배관 (pipe)
    - 가는 점선/파선 → 신호선 (signal)
    - 불확실 → unknown
    """
    width = line.get('width', 1.0)

    if width > 2.0:
        return 'pipe'
    elif width < 1.5:
        return 'signal'
    else:
        return 'unknown'


def classify_line_by_color(image: np.ndarray, line: Dict, sample_count: int = 10) -> Dict:
    """
    라인의 색상을 분석하여 유형 분류

    Args:
        image: BGR 이미지
        line: 라인 정보 (start_point, end_point)
        sample_count: 샘플링할 픽셀 수

    Returns:
        {'color': 'blue', 'type': 'water', 'confidence': 0.85, 'rgb': [0, 0, 255]}
    """
    x1, y1 = line['start_point']
    x2, y2 = line['end_point']
    h, w = image.shape[:2]

    # 라인을 따라 픽셀 샘플링
    samples = []
    for i in range(sample_count):
        t = i / max(sample_count - 1, 1)
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))

        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    samples.append(image[ny, nx])

    if not samples:
        return {'color': 'gray', 'type': 'unknown', 'confidence': 0.0, 'rgb': [128, 128, 128]}

    samples = np.array(samples)
    avg_color = np.mean(samples, axis=0).astype(np.uint8)
    b, g, r = avg_color

    hsv_pixel = cv2.cvtColor(np.uint8([[avg_color]]), cv2.COLOR_BGR2HSV)[0][0]
    h_val, s_val, v_val = hsv_pixel

    color_name = 'gray'
    confidence = 0.5

    if v_val < 50:
        color_name = 'black'
        confidence = 0.9
    elif s_val < 30:
        if v_val < 100:
            color_name = 'black'
            confidence = 0.8
        else:
            color_name = 'gray'
            confidence = 0.6
    else:
        if 0 <= h_val <= 10 or 170 <= h_val <= 180:
            color_name = 'red'
            confidence = 0.85
        elif 10 < h_val <= 25:
            color_name = 'orange'
            confidence = 0.80
        elif 25 < h_val <= 45:
            color_name = 'gray'
            confidence = 0.5
        elif 45 < h_val <= 85:
            color_name = 'green'
            confidence = 0.85
        elif 85 < h_val <= 105:
            color_name = 'cyan'
            confidence = 0.85
        elif 105 < h_val <= 130:
            color_name = 'blue'
            confidence = 0.85
        elif 130 < h_val <= 170:
            color_name = 'purple'
            confidence = 0.80

    line_info = LINE_COLOR_TYPES.get(color_name, LINE_COLOR_TYPES['gray'])

    return {
        'color': color_name,
        'type': line_info['name'],
        'type_korean': line_info['korean'],
        'confidence': confidence,
        'rgb': [int(r), int(g), int(b)],
        'hsv': [int(h_val), int(s_val), int(v_val)]
    }


def classify_all_lines_by_color(image: np.ndarray, lines: List[Dict]) -> List[Dict]:
    """
    모든 라인에 색상 분류 적용
    """
    for line in lines:
        color_info = classify_line_by_color(image, line)
        line['color'] = color_info['color']
        line['color_type'] = color_info['type']
        line['color_type_korean'] = color_info['type_korean']
        line['color_confidence'] = color_info['confidence']
        line['rgb'] = color_info['rgb']
        line['hsv'] = color_info['hsv']

    return lines


def classify_line_style(image: np.ndarray, line: Dict, sample_count: int = 30) -> Dict:
    """
    라인의 스타일(실선/점선/파선) 분류
    """
    x1, y1 = line['start_point']
    x2, y2 = line['end_point']

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    h, w = gray.shape

    # 라인을 따라 픽셀 밝기 샘플링
    intensities = []
    for i in range(sample_count):
        t = i / max(sample_count - 1, 1)
        x = int(x1 + t * (x2 - x1))
        y = int(y1 + t * (y2 - y1))

        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        vals = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    vals.append(gray[ny, nx])

        if vals:
            intensities.append(np.mean(vals))

    if len(intensities) < 5:
        return {
            'style': 'unknown',
            'style_korean': '미분류',
            'confidence': 0.0,
            'gap_ratio': 0.0,
            'pattern': []
        }

    intensities = np.array(intensities)
    sorted_vals = np.sort(intensities)
    bg_threshold = sorted_vals[int(len(sorted_vals) * 0.75)]
    is_line = intensities < bg_threshold - 20

    segments = []
    current_is_line = is_line[0]
    current_length = 1

    for i in range(1, len(is_line)):
        if is_line[i] == current_is_line:
            current_length += 1
        else:
            segments.append(('line' if current_is_line else 'gap', current_length))
            current_is_line = is_line[i]
            current_length = 1
    segments.append(('line' if current_is_line else 'gap', current_length))

    line_segments = [s[1] for s in segments if s[0] == 'line']
    gap_segments = [s[1] for s in segments if s[0] == 'gap']

    total_line = sum(line_segments) if line_segments else 0
    total_gap = sum(gap_segments) if gap_segments else 0
    total = total_line + total_gap

    gap_ratio = total_gap / total if total > 0 else 0
    num_gaps = len(gap_segments)

    style = 'unknown'
    confidence = 0.5

    if gap_ratio < 0.1:
        style = 'solid'
        confidence = 0.9 - gap_ratio
    elif gap_ratio < 0.3:
        if num_gaps >= 2:
            style = 'dashed'
            confidence = 0.7 + (0.3 - gap_ratio)
        else:
            style = 'solid'
            confidence = 0.7
    elif gap_ratio < 0.5:
        if num_gaps >= 5:
            avg_line_len = np.mean(line_segments) if line_segments else 0
            if avg_line_len < 3:
                style = 'dotted'
                confidence = 0.75
            else:
                style = 'dashed'
                confidence = 0.7
        else:
            style = 'dashed'
            confidence = 0.65
    else:
        if num_gaps >= 3:
            style = 'dotted'
            confidence = 0.6
        else:
            style = 'unknown'
            confidence = 0.4

    style_info = LINE_STYLE_TYPES.get(style, LINE_STYLE_TYPES['unknown'])

    return {
        'style': style,
        'style_korean': style_info['korean'],
        'signal_type': style_info['signal_type'],
        'confidence': round(confidence, 2),
        'gap_ratio': round(gap_ratio, 3),
        'num_gaps': num_gaps,
        'pattern': segments[:10]
    }


def classify_all_lines_by_style(image: np.ndarray, lines: List[Dict]) -> List[Dict]:
    """
    모든 라인에 스타일 분류 적용
    """
    for line in lines:
        style_info = classify_line_style(image, line)
        line['line_style'] = style_info['style']
        line['line_style_korean'] = style_info['style_korean']
        line['signal_type'] = style_info['signal_type']
        line['style_confidence'] = style_info['confidence']
        line['gap_ratio'] = style_info['gap_ratio']

    return lines


def classify_line_purpose(line: Dict) -> Dict:
    """
    라인의 용도 분류 (스타일 + 색상 조합)
    """
    style = line.get('line_style', 'unknown')
    color = line.get('color_type', 'unknown')

    purpose = 'unknown'

    if style == 'solid':
        if color in ['black', 'process']:
            purpose = 'main_process'
        elif color == 'green':
            purpose = 'hydraulic'
        else:
            purpose = 'secondary_process'
    elif style == 'dashed':
        if color == 'red':
            purpose = 'electrical'
        elif color == 'blue':
            purpose = 'pneumatic'
        elif color in ['black', 'signal']:
            purpose = 'instrument_signal'
        else:
            purpose = 'enclosure'
    elif style == 'dotted':
        purpose = 'software_link'
    elif style == 'dash_dot':
        purpose = 'boundary'

    purpose_info = LINE_PURPOSE_TYPES.get(purpose, LINE_PURPOSE_TYPES.get('main_process'))

    return {
        'purpose': purpose,
        'purpose_korean': purpose_info['korean'],
        'expected_weight': purpose_info['weight']
    }
