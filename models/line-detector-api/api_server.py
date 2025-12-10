"""
Line Detector API Server
P&ID 라인(배관/신호선) 검출 및 연결성 분석 API

기술:
- OpenCV Line Segment Detector (LSD)
- Hough Line Transform
- Line Thinning (Zhang-Suen Algorithm)
- Line Type Classification

포트: 5016
"""
import os
import io
import time
import logging
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np
from PIL import Image

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("LINE_DETECTOR_PORT", "5016"))


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class LineSegment(BaseModel):
    id: int
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    length: float
    angle: float
    line_type: str  # 'pipe', 'signal', 'unknown'
    confidence: float


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# Core Functions
# =====================

def thin_image(binary_img: np.ndarray) -> np.ndarray:
    """
    Zhang-Suen Thinning Algorithm
    이미지를 1픽셀 두께로 세선화
    """
    skeleton = cv2.ximgproc.thinning(binary_img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    return skeleton


def detect_lines_lsd(image: np.ndarray) -> List[Dict]:
    """
    Line Segment Detector (LSD) 사용
    더 정확한 라인 검출
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # LSD 생성
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    lines, widths, precs, nfas = lsd.detect(gray)

    results = []
    if lines is not None:
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

            results.append({
                'id': i,
                'start_point': (float(x1), float(y1)),
                'end_point': (float(x2), float(y2)),
                'length': float(length),
                'angle': float(angle),
                'width': float(widths[i][0]) if widths is not None else 1.0,
                'precision': float(precs[i][0]) if precs is not None else 0.0,
                'nfa': float(nfas[i][0]) if nfas is not None else 0.0
            })

    return results


def detect_lines_hough(image: np.ndarray, threshold: int = 50) -> List[Dict]:
    """
    Probabilistic Hough Line Transform
    빠른 라인 검출
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # 에지 검출
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # 확률적 Hough 변환
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold, minLineLength=30, maxLineGap=10)

    results = []
    if lines is not None:
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

            results.append({
                'id': i,
                'start_point': (float(x1), float(y1)),
                'end_point': (float(x2), float(y2)),
                'length': float(length),
                'angle': float(angle)
            })

    return results


def classify_line_type(line: Dict, all_lines: List[Dict]) -> str:
    """
    라인 유형 분류 (배관 vs 신호선)

    규칙 기반 분류:
    - 굵은 실선 → 배관 (pipe)
    - 가는 점선/파선 → 신호선 (signal)
    - 불확실 → unknown
    """
    width = line.get('width', 1.0)

    # 간단한 규칙 기반 분류
    # 실제로는 더 정교한 분류기 필요
    if width > 2.0:
        return 'pipe'
    elif width < 1.5:
        return 'signal'
    else:
        return 'unknown'


# P&ID 라인 색상 분류 기준
LINE_COLOR_TYPES = {
    'black': {'name': 'process', 'korean': '공정 라인', 'description': '주요 공정 배관'},
    'blue': {'name': 'water', 'korean': '냉각수/급수', 'description': '냉각수 또는 급수 라인'},
    'red': {'name': 'steam', 'korean': '증기/가열', 'description': '증기 또는 가열 라인'},
    'green': {'name': 'signal', 'korean': '신호선', 'description': '계장 신호 라인'},
    'orange': {'name': 'electrical', 'korean': '전기', 'description': '전기 배선'},
    'purple': {'name': 'drain', 'korean': '배수', 'description': '배수 라인'},
    'cyan': {'name': 'air', 'korean': '공기/가스', 'description': '압축공기 또는 가스 라인'},
    'gray': {'name': 'unknown', 'korean': '미분류', 'description': '분류되지 않은 라인'},
}


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

        # 범위 체크
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        # 주변 픽셀도 포함 (3x3)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    samples.append(image[ny, nx])

    if not samples:
        return {'color': 'gray', 'type': 'unknown', 'confidence': 0.0, 'rgb': [128, 128, 128]}

    # 평균 색상 계산
    samples = np.array(samples)
    avg_color = np.mean(samples, axis=0).astype(np.uint8)  # BGR
    b, g, r = avg_color

    # HSV 변환
    hsv_pixel = cv2.cvtColor(np.uint8([[avg_color]]), cv2.COLOR_BGR2HSV)[0][0]
    h_val, s_val, v_val = hsv_pixel

    # 색상 분류
    color_name = 'gray'
    confidence = 0.5

    # 밝기가 낮으면 검은색 (공정 라인)
    if v_val < 50:
        color_name = 'black'
        confidence = 0.9
    # 채도가 낮으면 회색/검은색
    elif s_val < 30:
        if v_val < 100:
            color_name = 'black'
            confidence = 0.8
        else:
            color_name = 'gray'
            confidence = 0.6
    else:
        # HSV 색상 범위로 분류
        if 0 <= h_val <= 10 or 170 <= h_val <= 180:
            color_name = 'red'
            confidence = 0.85
        elif 10 < h_val <= 25:
            color_name = 'orange'
            confidence = 0.80
        elif 25 < h_val <= 45:
            # 노란색은 보통 배경이므로 무시
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

    Args:
        image: BGR 이미지
        lines: 라인 목록

    Returns:
        색상 정보가 추가된 라인 목록
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


# P&ID 라인 스타일 분류 기준
LINE_STYLE_TYPES = {
    'solid': {'korean': '실선', 'description': '주요 공정 배관', 'signal_type': 'process'},
    'dashed': {'korean': '점선', 'description': '계장 신호선', 'signal_type': 'instrument'},
    'dotted': {'korean': '점점선', 'description': '보조/옵션 라인', 'signal_type': 'auxiliary'},
    'dash_dot': {'korean': '일점쇄선', 'description': '경계선/중심선', 'signal_type': 'centerline'},
    'unknown': {'korean': '미분류', 'description': '분류 불가', 'signal_type': 'unknown'},
}


def classify_line_style(image: np.ndarray, line: Dict, sample_count: int = 30) -> Dict:
    """
    라인의 스타일(실선/점선/파선) 분류

    원리: 라인을 따라 픽셀 밝기를 샘플링하여 패턴 분석
    - 실선: 연속적으로 어두운 픽셀
    - 점선: 규칙적인 밝기 변화 (긴 간격)
    - 점점선: 짧은 간격의 밝기 변화

    Args:
        image: BGR 또는 Grayscale 이미지
        line: 라인 정보 (start_point, end_point)
        sample_count: 샘플링 포인트 수

    Returns:
        {'style': 'dashed', 'korean': '점선', 'confidence': 0.85, 'gap_ratio': 0.3}
    """
    x1, y1 = line['start_point']
    x2, y2 = line['end_point']

    # Grayscale 변환
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

        # 범위 체크
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        # 라인 주변 픽셀 평균 (노이즈 감소)
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

    # 배경 밝기 추정 (상위 25% 평균)
    sorted_vals = np.sort(intensities)
    bg_threshold = sorted_vals[int(len(sorted_vals) * 0.75)]

    # 라인 픽셀 vs 배경 픽셀 분류
    # 라인 픽셀은 배경보다 어두움
    is_line = intensities < bg_threshold - 20  # 20 이상 어두우면 라인

    # 패턴 분석: 연속된 라인/배경 구간 찾기
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

    # 스타일 분류
    line_segments = [s[1] for s in segments if s[0] == 'line']
    gap_segments = [s[1] for s in segments if s[0] == 'gap']

    total_line = sum(line_segments) if line_segments else 0
    total_gap = sum(gap_segments) if gap_segments else 0
    total = total_line + total_gap

    gap_ratio = total_gap / total if total > 0 else 0
    num_gaps = len(gap_segments)

    # 분류 기준
    style = 'unknown'
    confidence = 0.5

    if gap_ratio < 0.1:
        # 거의 연속: 실선
        style = 'solid'
        confidence = 0.9 - gap_ratio
    elif gap_ratio < 0.3:
        # 약간의 갭: 점선일 가능성
        if num_gaps >= 2:
            style = 'dashed'
            confidence = 0.7 + (0.3 - gap_ratio)
        else:
            style = 'solid'
            confidence = 0.7
    elif gap_ratio < 0.5:
        # 많은 갭: 점선 또는 점점선
        if num_gaps >= 5:
            # 많은 짧은 세그먼트: 점점선
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
        # 갭이 너무 많음: 점점선 또는 노이즈
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
        'pattern': segments[:10]  # 처음 10개 세그먼트만
    }


def classify_all_lines_by_style(image: np.ndarray, lines: List[Dict]) -> List[Dict]:
    """
    모든 라인에 스타일 분류 적용

    Args:
        image: BGR 이미지
        lines: 라인 목록

    Returns:
        스타일 정보가 추가된 라인 목록
    """
    for line in lines:
        style_info = classify_line_style(image, line)
        line['line_style'] = style_info['style']
        line['line_style_korean'] = style_info['style_korean']
        line['signal_type'] = style_info['signal_type']
        line['style_confidence'] = style_info['confidence']
        line['gap_ratio'] = style_info['gap_ratio']

    return lines


def _order_segments_to_path(segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                            tolerance: float = 25.0) -> List[Tuple[float, float]]:
    """
    분리된 세그먼트들을 연결하여 순서대로 정렬된 경로 생성
    점들이 정확히 일치하지 않아도 tolerance 내에서 연결

    Args:
        segments: [(start, end), ...] 형태의 세그먼트 리스트
        tolerance: 연결로 간주할 최대 거리

    Returns:
        순서대로 연결된 점들의 리스트
    """
    if not segments:
        return []

    if len(segments) == 1:
        return [segments[0][0], segments[0][1]]

    # 모든 세그먼트를 사용 가능한 목록으로
    remaining = list(segments)

    # 첫 세그먼트로 시작
    first = remaining.pop(0)
    path = [first[0], first[1]]

    def distance(p1, p2):
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def find_closest_segment(point, segments, tolerance):
        """point에 가장 가까운 세그먼트의 끝점 찾기"""
        best_dist = float('inf')
        best_idx = -1
        best_end = None  # 'start' or 'end'

        for i, seg in enumerate(segments):
            d_start = distance(point, seg[0])
            d_end = distance(point, seg[1])

            if d_start < best_dist and d_start <= tolerance:
                best_dist = d_start
                best_idx = i
                best_end = 'start'
            if d_end < best_dist and d_end <= tolerance:
                best_dist = d_end
                best_idx = i
                best_end = 'end'

        return best_idx, best_end

    # 경로 확장 - 앞뒤로 세그먼트 연결
    changed = True
    while changed and remaining:
        changed = False

        # 경로 끝에서 연결 시도
        idx, end = find_closest_segment(path[-1], remaining, tolerance)
        if idx >= 0:
            seg = remaining.pop(idx)
            if end == 'start':
                path.append(seg[1])  # start는 가까우니 end 추가
            else:
                path.append(seg[0])  # end가 가까우니 start 추가
            changed = True
            continue

        # 경로 시작에서 연결 시도
        idx, end = find_closest_segment(path[0], remaining, tolerance)
        if idx >= 0:
            seg = remaining.pop(idx)
            if end == 'start':
                path.insert(0, seg[1])
            else:
                path.insert(0, seg[0])
            changed = True

    return path


def merge_collinear_lines(lines: List[Dict], angle_threshold: float = 5.0,
                          distance_threshold: float = 20.0) -> List[Dict]:
    """
    공선(collinear) 라인 병합
    여러 조각으로 분리된 라인을 하나로 합침
    """
    if not lines:
        return lines

    merged = []
    used = set()

    for i, line1 in enumerate(lines):
        if i in used:
            continue

        current_group = [line1]
        used.add(i)

        for j, line2 in enumerate(lines):
            if j in used:
                continue

            # 각도 차이 확인
            angle_diff = abs(line1['angle'] - line2['angle'])
            if angle_diff > 90:
                angle_diff = 180 - angle_diff

            if angle_diff < angle_threshold:
                # 거리 확인 (끝점 간)
                min_dist = min(
                    np.sqrt((line1['end_point'][0] - line2['start_point'][0])**2 +
                           (line1['end_point'][1] - line2['start_point'][1])**2),
                    np.sqrt((line1['start_point'][0] - line2['end_point'][0])**2 +
                           (line1['start_point'][1] - line2['end_point'][1])**2)
                )

                if min_dist < distance_threshold:
                    current_group.append(line2)
                    used.add(j)

        # 그룹 병합
        if len(current_group) == 1:
            # 단일 라인도 waypoints 형식으로 통일
            single_line = current_group[0].copy()
            single_line['waypoints'] = [
                list(single_line['start_point']),
                list(single_line['end_point'])
            ]
            merged.append(single_line)
        else:
            # 연결된 라인들의 점들을 순서대로 연결
            # 각 라인의 시작점/끝점을 그래프로 구성하여 경로 찾기
            all_segments = []
            for l in current_group:
                all_segments.append((tuple(l['start_point']), tuple(l['end_point'])))

            # 점들을 순서대로 연결하여 경로 생성
            ordered_points = _order_segments_to_path(all_segments)

            if len(ordered_points) >= 2:
                start_pt = ordered_points[0]
                end_pt = ordered_points[-1]

                # 전체 경로 길이 계산
                total_length = 0
                for i in range(len(ordered_points) - 1):
                    p1, p2 = ordered_points[i], ordered_points[i+1]
                    total_length += np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

                # 전체 방향 (시작-끝 기준)
                angle = np.degrees(np.arctan2(end_pt[1]-start_pt[1], end_pt[0]-start_pt[0]))

                merged_line = {
                    'id': len(merged),
                    'start_point': start_pt,
                    'end_point': end_pt,
                    'waypoints': [list(p) for p in ordered_points],  # 중간 점 보존
                    'length': float(total_length),
                    'angle': float(angle),
                    'merged_count': len(current_group)
                }
                merged.append(merged_line)
            else:
                # fallback: 기존 방식
                all_points = []
                for l in current_group:
                    all_points.extend([l['start_point'], l['end_point']])
                all_points = np.array(all_points)
                mean = np.mean(all_points, axis=0)
                centered = all_points - mean
                cov = np.cov(centered.T)
                eigenvalues, eigenvectors = np.linalg.eig(cov)
                main_axis = eigenvectors[:, np.argmax(eigenvalues)]
                projections = np.dot(centered, main_axis)
                min_idx = np.argmin(projections)
                max_idx = np.argmax(projections)

                merged_line = {
                    'id': len(merged),
                    'start_point': tuple(all_points[min_idx]),
                    'end_point': tuple(all_points[max_idx]),
                    'waypoints': [list(all_points[min_idx]), list(all_points[max_idx])],
                    'length': float(np.linalg.norm(all_points[max_idx] - all_points[min_idx])),
                    'angle': float(np.degrees(np.arctan2(main_axis[1], main_axis[0]))),
                    'merged_count': len(current_group)
                }
                merged.append(merged_line)

    return merged


def find_intersections(lines: List[Dict]) -> List[Dict]:
    """
    라인 교차점 찾기
    """
    intersections = []

    for i, line1 in enumerate(lines):
        for j, line2 in enumerate(lines):
            if i >= j:
                continue

            # 두 라인의 교차점 계산
            x1, y1 = line1['start_point']
            x2, y2 = line1['end_point']
            x3, y3 = line2['start_point']
            x4, y4 = line2['end_point']

            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                continue  # 평행

            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

            if 0 <= t <= 1 and 0 <= u <= 1:
                px = x1 + t * (x2 - x1)
                py = y1 + t * (y2 - y1)

                intersections.append({
                    'point': (float(px), float(py)),
                    'line1_id': line1['id'],
                    'line2_id': line2['id']
                })

    return intersections


def visualize_lines(image: np.ndarray, lines: List[Dict],
                    intersections: List[Dict] = None) -> np.ndarray:
    """
    라인 검출 결과 시각화 - waypoints가 있으면 polyline으로 그림
    """
    vis = image.copy()

    # 라인 색상 (유형별)
    colors = {
        'pipe': (0, 0, 255),      # Red
        'signal': (255, 0, 0),    # Blue
        'unknown': (0, 255, 0)    # Green
    }

    for line in lines:
        line_type = line.get('line_type', 'unknown')
        color = colors.get(line_type, (0, 255, 0))

        # waypoints가 있으면 polyline으로 그림, 없으면 직선
        if 'waypoints' in line and len(line['waypoints']) >= 2:
            pts = np.array([[int(p[0]), int(p[1])] for p in line['waypoints']], dtype=np.int32)
            cv2.polylines(vis, [pts], isClosed=False, color=color, thickness=2)
        else:
            pt1 = (int(line['start_point'][0]), int(line['start_point'][1]))
            pt2 = (int(line['end_point'][0]), int(line['end_point'][1]))
            cv2.line(vis, pt1, pt2, color, 2)

    # 교차점 표시
    if intersections:
        for inter in intersections:
            pt = (int(inter['point'][0]), int(inter['point'][1]))
            cv2.circle(vis, pt, 5, (255, 255, 0), -1)  # Yellow

    return vis


def numpy_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 변환"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Line Detector API",
    description="P&ID 라인(배관/신호선) 검출 및 연결성 분석 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="line-detector-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "line-detector",
        "name": "Line Detector",
        "display_name": "P&ID Line Detector",
        "version": "1.0.0",
        "description": "P&ID 라인(배관/신호선) 검출 및 연결성 분석 API",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/process",
        "method": "POST",
        "requires_image": True,
        "blueprintflow": {
            "category": "segmentation",
            "color": "#8b5cf6",
            "icon": "GitCommitHorizontal"
        },
        "inputs": [
            {"name": "image", "type": "Image", "required": True, "description": "P&ID 도면 이미지"}
        ],
        "outputs": [
            {"name": "lines", "type": "LineSegment[]", "description": "검출된 라인 목록"},
            {"name": "intersections", "type": "Intersection[]", "description": "교차점 목록"},
            {"name": "visualization", "type": "Image", "description": "시각화 이미지"}
        ],
        "parameters": [
            {"name": "method", "type": "select", "options": ["lsd", "hough", "combined"], "default": "lsd"},
            {"name": "merge_lines", "type": "boolean", "default": True},
            {"name": "classify_types", "type": "boolean", "default": True},
            {"name": "classify_colors", "type": "boolean", "default": True, "description": "색상 기반 라인 분류"},
            {"name": "classify_styles", "type": "boolean", "default": True, "description": "스타일 분류 (실선/점선)"},
            {"name": "find_intersections", "type": "boolean", "default": True},
            {"name": "visualize", "type": "boolean", "default": True},
            {"name": "min_length", "type": "number", "default": 0, "description": "최소 라인 길이 (픽셀). 0=필터링 안함"},
            {"name": "max_lines", "type": "number", "default": 0, "description": "최대 라인 수 제한. 0=제한 없음"}
        ]
    }


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    method: str = Form(default="lsd", description="검출 방식 (lsd, hough, combined)"),
    merge_lines: bool = Form(default=True, description="공선 라인 병합"),
    classify_types: bool = Form(default=True, description="라인 유형 분류 (배관/신호선)"),
    classify_colors: bool = Form(default=True, description="색상 기반 라인 분류 (공정/냉각/증기/신호 등)"),
    classify_styles: bool = Form(default=True, description="스타일 분류 (실선/점선/점점선)"),
    find_intersections_flag: bool = Form(default=True, alias="find_intersections", description="교차점 검출"),
    visualize: bool = Form(default=True, description="결과 시각화"),
    min_length: float = Form(default=0, description="최소 라인 길이 (픽셀). 0=필터링 안함"),
    max_lines: int = Form(default=0, description="최대 라인 수 제한. 0=제한 없음")
):
    """
    P&ID 라인 검출 메인 엔드포인트

    기능:
    - LSD/Hough 기반 라인 검출
    - 라인 유형 분류 (배관 vs 신호선)
    - 색상 기반 라인 분류 (공정/냉각/증기/신호선 등)
    - 스타일 분류 (실선/점선/점점선)
    - 공선 라인 병합
    - 교차점 검출
    """
    start_time = time.time()

    try:
        # 이미지 로드
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        logger.info(f"Processing image: {file.filename}, size: {image.shape}")

        # 라인 검출
        if method == "lsd":
            lines = detect_lines_lsd(image)
        elif method == "hough":
            lines = detect_lines_hough(image)
        else:  # combined
            lsd_lines = detect_lines_lsd(image)
            hough_lines = detect_lines_hough(image)
            lines = lsd_lines + hough_lines

        logger.info(f"Detected {len(lines)} lines using {method}")

        # 공선 라인 병합
        if merge_lines:
            original_count = len(lines)
            lines = merge_collinear_lines(lines)
            logger.info(f"Merged lines: {original_count} -> {len(lines)}")

        # 최소 길이 필터링
        if min_length > 0:
            original_count = len(lines)
            lines = [l for l in lines if l.get('length', 0) >= min_length]
            logger.info(f"Length filter (>= {min_length}px): {original_count} -> {len(lines)}")

        # 최대 라인 수 제한 (길이 기준 정렬 후 상위 N개)
        if max_lines > 0 and len(lines) > max_lines:
            original_count = len(lines)
            lines = sorted(lines, key=lambda l: l.get('length', 0), reverse=True)[:max_lines]
            # ID 재할당
            for i, line in enumerate(lines):
                line['id'] = i
            logger.info(f"Max lines limit ({max_lines}): {original_count} -> {len(lines)}")

        # 라인 유형 분류
        if classify_types:
            for line in lines:
                line['line_type'] = classify_line_type(line, lines)
                line['confidence'] = 0.85  # 기본 신뢰도

        # 색상 기반 라인 분류
        if classify_colors:
            lines = classify_all_lines_by_color(image, lines)
            logger.info(f"Color classification applied to {len(lines)} lines")

        # 스타일 분류 (실선/점선)
        if classify_styles:
            lines = classify_all_lines_by_style(image, lines)
            logger.info(f"Style classification applied to {len(lines)} lines")

        # 교차점 검출
        intersections = []
        if find_intersections_flag:
            intersections = find_intersections(lines)
            logger.info(f"Found {len(intersections)} intersections")

        # 시각화
        visualization_base64 = None
        if visualize:
            vis_image = visualize_lines(image, lines, intersections)
            visualization_base64 = numpy_to_base64(vis_image)

        # 통계 계산
        pipe_count = sum(1 for l in lines if l.get('line_type') == 'pipe')
        signal_count = sum(1 for l in lines if l.get('line_type') == 'signal')
        unknown_count = sum(1 for l in lines if l.get('line_type') == 'unknown')

        # 색상 기반 통계
        color_stats = {}
        if classify_colors:
            from collections import Counter
            color_counts = Counter(l.get('color_type', 'unknown') for l in lines)
            color_stats = {
                "by_color_type": dict(color_counts),
                "process_lines": color_counts.get('process', 0),
                "water_lines": color_counts.get('water', 0),
                "steam_lines": color_counts.get('steam', 0),
                "signal_lines_color": color_counts.get('signal', 0),
                "electrical_lines": color_counts.get('electrical', 0),
                "air_lines": color_counts.get('air', 0),
            }

        # 스타일 기반 통계
        style_stats = {}
        if classify_styles:
            from collections import Counter
            style_counts = Counter(l.get('line_style', 'unknown') for l in lines)
            style_stats = {
                "by_line_style": dict(style_counts),
                "solid_lines": style_counts.get('solid', 0),
                "dashed_lines": style_counts.get('dashed', 0),
                "dotted_lines": style_counts.get('dotted', 0),
                "unknown_style_lines": style_counts.get('unknown', 0),
            }

        processing_time = time.time() - start_time

        result = {
            "lines": lines,
            "intersections": intersections,
            "statistics": {
                "total_lines": len(lines),
                "pipe_lines": pipe_count,
                "signal_lines": signal_count,
                "unknown_lines": unknown_count,
                "intersection_count": len(intersections),
                **color_stats,
                **style_stats
            },
            "visualization": visualization_base64,
            "method": method,
            "image_size": {"width": image.shape[1], "height": image.shape[0]}
        }

        return ProcessResponse(
            success=True,
            data=result,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Processing error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Line Detector API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
