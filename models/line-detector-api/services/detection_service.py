"""
Line Detection Service
라인 검출 및 병합 함수
"""

import logging
from typing import List, Dict, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _safe_to_gray(img: np.ndarray) -> np.ndarray:
    """Safely convert image to grayscale, handling edge cases."""
    if img is None or img.size == 0:
        return img
    if len(img.shape) == 2:
        return img
    if img.shape[2] == 1:
        return img[:, :, 0]
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


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
    gray = _safe_to_gray(image)

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
    gray = _safe_to_gray(image)

    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
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


def _order_segments_to_path(segments: List[Tuple[Tuple[float, float], Tuple[float, float]]],
                            tolerance: float = 25.0) -> List[Tuple[float, float]]:
    """
    분리된 세그먼트들을 연결하여 순서대로 정렬된 경로 생성
    """
    if not segments:
        return []

    if len(segments) == 1:
        return [segments[0][0], segments[0][1]]

    remaining = list(segments)
    first = remaining.pop(0)
    path = [first[0], first[1]]

    def distance(p1, p2):
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def find_closest_segment(point, segs, tol):
        best_dist = float('inf')
        best_idx = -1
        best_end = None

        for i, seg in enumerate(segs):
            d_start = distance(point, seg[0])
            d_end = distance(point, seg[1])

            if d_start < best_dist and d_start <= tol:
                best_dist = d_start
                best_idx = i
                best_end = 'start'
            if d_end < best_dist and d_end <= tol:
                best_dist = d_end
                best_idx = i
                best_end = 'end'

        return best_idx, best_end

    changed = True
    while changed and remaining:
        changed = False

        idx, end = find_closest_segment(path[-1], remaining, tolerance)
        if idx >= 0:
            seg = remaining.pop(idx)
            if end == 'start':
                path.append(seg[1])
            else:
                path.append(seg[0])
            changed = True
            continue

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

            angle_diff = abs(line1['angle'] - line2['angle'])
            if angle_diff > 90:
                angle_diff = 180 - angle_diff

            if angle_diff < angle_threshold:
                min_dist = min(
                    np.sqrt((line1['end_point'][0] - line2['start_point'][0])**2 +
                           (line1['end_point'][1] - line2['start_point'][1])**2),
                    np.sqrt((line1['start_point'][0] - line2['end_point'][0])**2 +
                           (line1['start_point'][1] - line2['end_point'][1])**2)
                )

                if min_dist < distance_threshold:
                    current_group.append(line2)
                    used.add(j)

        if len(current_group) == 1:
            single_line = current_group[0].copy()
            single_line['waypoints'] = [
                list(single_line['start_point']),
                list(single_line['end_point'])
            ]
            merged.append(single_line)
        else:
            all_segments = []
            for l in current_group:
                all_segments.append((tuple(l['start_point']), tuple(l['end_point'])))

            ordered_points = _order_segments_to_path(all_segments)

            if len(ordered_points) >= 2:
                start_pt = ordered_points[0]
                end_pt = ordered_points[-1]

                total_length = 0
                for idx in range(len(ordered_points) - 1):
                    p1, p2 = ordered_points[idx], ordered_points[idx+1]
                    total_length += np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)

                angle = np.degrees(np.arctan2(end_pt[1]-start_pt[1], end_pt[0]-start_pt[0]))

                merged_line = {
                    'id': len(merged),
                    'start_point': start_pt,
                    'end_point': end_pt,
                    'waypoints': [list(p) for p in ordered_points],
                    'length': float(total_length),
                    'angle': float(angle),
                    'merged_count': len(current_group)
                }
                merged.append(merged_line)
            else:
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

            x1, y1 = line1['start_point']
            x2, y2 = line1['end_point']
            x3, y3 = line2['start_point']
            x4, y4 = line2['end_point']

            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                continue

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
