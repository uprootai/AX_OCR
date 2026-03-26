"""
BMT GAR 배치도 뷰 자동 분리기

입력: GAR 배치도 이미지 (래스터 PNG)
출력: 뷰별 크롭 이미지 리스트 + 유동적 경계 시각화

방법론:
1. PaddleOCR로 뷰 라벨 자동 검출 ("FRONT VIEW", "TOP VIEW" 등)
2. 라벨 좌표로 그리드 행/열 추정
3. 빈공간 프로파일로 경계 정교화
4. 그리드 크롭 + 하단 보충 크롭
5. hull 마스킹 없이 bbox 크롭 (경계 TAG 보존)

하드코딩: 0개 (모든 좌표는 이미지에서 동적 계산)
"""
import numpy as np
from PIL import Image
import cv2
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ViewRegion:
    name: str
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    hull: Optional[np.ndarray] = None


def detect_view_labels(image_path: str, ocr_url: str = "http://localhost:5006/api/v1/ocr") -> list[dict]:
    """PaddleOCR로 뷰 라벨 텍스트 위치 검출"""
    import requests

    with open(image_path, 'rb') as f:
        r = requests.post(ocr_url, files={'file': ('img.png', f, 'image/png')}, timeout=120).json()

    view_pattern = re.compile(r'(?:TOP|FRONT|RIGHT|BOTTOM|LEFT)\s*VIEW|\'?A\'?\s*VIEW', re.IGNORECASE)

    labels = []
    for det in r.get('detections', []):
        text = det['text'].strip()
        if view_pattern.search(text):
            bbox = det['bbox']
            x1, y1 = bbox[0]
            x3, y3 = bbox[2]
            labels.append({
                'text': text,
                'cx': (x1 + x3) / 2,
                'cy': (y1 + y3) / 2,
                'bbox': (x1, y1, x3, y3),
            })

    return labels


def cluster_labels_to_grid(labels: list[dict]) -> tuple[list[float], list[float]]:
    """라벨 좌표를 행/열로 클러스터링"""
    if not labels:
        return [], []

    # y좌표 클러스터링 (행)
    ys = sorted(set(l['cy'] for l in labels))
    rows = []
    current_cluster = [ys[0]]
    for y in ys[1:]:
        if y - current_cluster[-1] < 100:  # 100px 이내는 같은 행
            current_cluster.append(y)
        else:
            rows.append(np.mean(current_cluster))
            current_cluster = [y]
    rows.append(np.mean(current_cluster))

    # x좌표 클러스터링 (열)
    xs = sorted(set(l['cx'] for l in labels))
    cols = []
    current_cluster = [xs[0]]
    for x in xs[1:]:
        if x - current_cluster[-1] < 100:
            current_cluster.append(x)
        else:
            cols.append(np.mean(current_cluster))
            current_cluster = [x]
    cols.append(np.mean(current_cluster))

    return rows, cols


def find_blank_boundary(gray: np.ndarray, target: float, axis: str,
                        search_range: int = 150, min_gap: int = 8,
                        threshold: int = 248) -> int:
    """target 좌표 근처에서 빈 공간(밝은 행/열)을 찾아 경계 반환"""
    h, w = gray.shape

    if axis == 'horizontal':
        # 행별 평균 밝기
        means = np.mean(gray, axis=1)
        start = max(0, int(target - search_range))
        end = min(h, int(target + search_range))
    else:
        means = np.mean(gray, axis=0)
        start = max(0, int(target - search_range))
        end = min(w, int(target + search_range))

    # target에 가장 가까운 빈 구간 찾기
    best_mid = int(target)
    best_gap = 0

    gap_start = None
    for i in range(start, end):
        if means[i] > threshold:
            if gap_start is None:
                gap_start = i
        else:
            if gap_start is not None and i - gap_start >= min_gap:
                mid = (gap_start + i) // 2
                gap_width = i - gap_start
                if gap_width > best_gap:
                    best_gap = gap_width
                    best_mid = mid
            gap_start = None

    return best_mid


def find_outer_border(gray: np.ndarray, threshold: int = 200) -> tuple[int, int, int, int]:
    """이미지 외곽 테두리 내부 영역 찾기"""
    h, w = gray.shape
    row_means = np.mean(gray, axis=1)
    col_means = np.mean(gray, axis=0)

    # 상단: 밝기가 낮아지는(도면 시작) 첫 행
    top = 0
    for y in range(h):
        if row_means[y] < 240:
            top = max(0, y - 2)
            break

    # 하단
    bottom = h
    for y in range(h-1, 0, -1):
        if row_means[y] < 240:
            bottom = min(h, y + 2)
            break

    # 좌측
    left = 0
    for x in range(w):
        if col_means[x] < 240:
            left = max(0, x - 2)
            break

    # 우측
    right = w
    for x in range(w-1, 0, -1):
        if col_means[x] < 240:
            right = min(w, x + 2)
            break

    return top, bottom, left, right


def find_lower_boundary(gray: np.ndarray, grid_bottom_y: int, threshold: int = 248) -> int:
    """그리드 아래 하단 경계 (title block 상단) 찾기"""
    h, w = gray.shape
    row_means = np.mean(gray, axis=1)

    # grid_bottom_y 아래에서 마지막 넓은 빈 구간 찾기
    last_blank_start = h
    gap_start = None
    for y in range(grid_bottom_y, h):
        if row_means[y] > threshold:
            if gap_start is None:
                gap_start = y
        else:
            if gap_start is not None and y - gap_start >= 10:
                last_blank_start = y
            gap_start = None

    return min(last_blank_start, h - 50)


def split_gar_views(image_path: str, ocr_url: str = "http://localhost:5006/api/v1/ocr") -> list[ViewRegion]:
    """
    GAR 배치도 이미지를 뷰별로 자동 분리

    Args:
        image_path: GAR 배치도 PNG 경로
        ocr_url: PaddleOCR API 엔드포인트

    Returns:
        ViewRegion 리스트 (name, bbox, hull)
    """
    img = Image.open(image_path)
    gray = np.array(img.convert('L'))
    h, w = gray.shape
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Step 1: 뷰 라벨 검출
    labels = detect_view_labels(image_path, ocr_url)
    if not labels:
        # 라벨 못 찾으면 전체 이미지 반환
        return [ViewRegion('FULL', (0, 0, w, h))]

    # Step 2: 행/열 클러스터링
    rows, cols = cluster_labels_to_grid(labels)

    # Step 3: 외곽 테두리
    outer_t, outer_b, outer_l, outer_r = find_outer_border(gray)

    # Step 4: 행/열 경계 정교화 (빈공간 프로파일)
    h_boundaries = []
    for i in range(len(rows) - 1):
        target = (rows[i] + rows[i+1]) / 2
        boundary = find_blank_boundary(gray, target, 'horizontal')
        h_boundaries.append(boundary)

    v_boundaries = []
    for i in range(len(cols) - 1):
        target = (cols[i] + cols[i+1]) / 2
        boundary = find_blank_boundary(gray, target, 'vertical')
        v_boundaries.append(boundary)

    # Step 5: 마지막 행 아래 경계 (마지막 라벨 행 아래 빈공간)
    last_row_y = rows[-1]
    # 마지막 행 라벨 아래에서 빈 공간 찾기 (그리드 하단 경계)
    grid_bottom = find_blank_boundary(gray, last_row_y + 200, 'horizontal', search_range=300)
    if grid_bottom <= (h_boundaries[-1] if h_boundaries else 0):
        grid_bottom = int(last_row_y + 300)  # fallback

    lower_boundary = find_lower_boundary(gray, grid_bottom)

    # Step 6: 그리드 영역 생성
    y_edges = [outer_t] + h_boundaries + [grid_bottom]
    x_edges = [outer_l] + v_boundaries + [outer_r]

    regions = []
    row_names = ['upper', 'mid', 'lower']

    for ri in range(len(y_edges) - 1):
        for ci in range(len(x_edges) - 1):
            y1, y2 = y_edges[ri], y_edges[ri + 1]
            x1, x2 = x_edges[ci], x_edges[ci + 1]

            if y2 - y1 < 50 or x2 - x1 < 50:
                continue

            # 라벨 이름 매칭
            name = f"view_{ri}_{ci}"
            for label in labels:
                if x1 <= label['cx'] <= x2 and y1 <= label['cy'] <= y2:
                    name = label['text'].strip()
                    break

            # hull 생성 (시각화용)
            roi_bin = binary[y1:y2, x1:x2]
            hull = None
            if roi_bin.size > 0:
                kernel = np.ones((10, 10), np.uint8)
                roi_d = cv2.dilate(roi_bin, kernel, iterations=2)
                cnts, _ = cv2.findContours(roi_d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if cnts:
                    biggest = max(cnts, key=cv2.contourArea)
                    biggest[:, :, 0] += x1
                    biggest[:, :, 1] += y1
                    hull = cv2.convexHull(biggest)

            regions.append(ViewRegion(name, (x1, y1, x2, y2), hull))

    # Step 7: 하단 보충 크롭 (3D 투시도 영역)
    # 하단 영역을 전체 + 좌/우 절반으로 분할하여 작은 TAG도 검출
    if grid_bottom < outer_b - 100:
        lower_box = (outer_l, grid_bottom - 50, outer_r, lower_boundary)
        regions.append(ViewRegion('LOWER_FULL', lower_box, None))

        mid_x = (outer_l + outer_r) // 2
        regions.append(ViewRegion(
            'LOWER_LEFT',
            (outer_l, grid_bottom - 50, mid_x, lower_boundary),
            None
        ))
        regions.append(ViewRegion(
            'LOWER_RIGHT',
            (mid_x - 100, grid_bottom - 50, outer_r, lower_boundary),
            None
        ))

    return regions


if __name__ == '__main__':
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/gar-page3.png'

    print(f"Processing: {image_path}")
    regions = split_gar_views(image_path)

    print(f"\n{len(regions)} regions detected:")
    for r in regions:
        x1, y1, x2, y2 = r.bbox
        print(f"  {r.name}: [{x1},{y1},{x2},{y2}] ({x2-x1}x{y2-y1}) hull={'Yes' if r.hull is not None else 'No'}")
