"""Randomized Hough Transform(RHT) 기반 원/호 검출 모듈

베어링 도면에서 부분 호(arc)를 포함한 원을 검출한다.
RANSAC(3점 샘플)과 달리 2점 + 기울기 방향으로 중심을 투표, 어큐뮬레이터 피크로 원 추출.
참고: A Fast Randomized Hough Transform for Circle/Circular Arc Recognition
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# --- 1. 에지 + 그래디언트 ---

def compute_edge_gradients(
    img_gray: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Canny 에지 검출(30,100) + Sobel 그래디언트 추출

    Returns:
        edge_points: (N, 2) 배열 [x, y]
        grad_dx:     (N,)   Sobel x-방향
        grad_dy:     (N,)   Sobel y-방향
    """
    blurred = cv2.GaussianBlur(img_gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 30, 100)
    sobel_dx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    sobel_dy = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)

    ys, xs = np.where(edges > 0)
    if len(xs) == 0:
        empty = np.zeros((0, 2), dtype=np.float64)
        return empty, np.zeros(0), np.zeros(0)

    edge_points = np.column_stack([xs, ys]).astype(np.float64)
    logger.debug("에지 포인트 수: %d", len(edge_points))
    return edge_points, sobel_dx[ys, xs], sobel_dy[ys, xs]


# --- 2. 법선 교차점 ---

def _normals_intersection(
    p1: np.ndarray, dx1: float, dy1: float,
    p2: np.ndarray, dx2: float, dy2: float,
) -> Optional[Tuple[float, float]]:
    """두 에지 점의 그래디언트(법선) 방향 직선 교차점 계산.
    평행선이면 None 반환.

    p_i + t_i*(dx_i, dy_i) 형태의 연립방정식을 크라메르 공식으로 풀이.
    """
    det = dx1 * (-dy2) - (-dx2) * dy1
    if abs(det) < 1e-10:
        return None
    bx, by = p2[0] - p1[0], p2[1] - p1[1]
    t = (bx * (-dy2) - (-dx2) * by) / det
    return (p1[0] + t * dx1, p1[1] + t * dy1)


# --- 3. RHT 투표 ---

def rht_circle_detect(
    edge_points: np.ndarray,
    grad_dx: np.ndarray,
    grad_dy: np.ndarray,
    max_iter: int = 3000,
    bin_size: int = 5,
    vote_threshold: int = 8,
    r_min: int = 20,
    r_max: int = 2000,
) -> List[Tuple[float, float, float, float]]:
    """Randomized Hough Transform — 2점 + 법선으로 원 중심 투표

    알고리즘:
      1. 에지 점 2개 무작위 샘플
      2. 두 법선 교차점 = 원 중심 후보, 평균 거리 = 반지름 후보
      3. r_min ≤ r ≤ r_max이면 2D 어큐뮬레이터(bin_size 해상도)에 투표
      4. vote_threshold 이상 피크 추출
      5. 피크 주변 inlier로 Kasa 최소자승 정제

    Returns:
        [(cx, cy, r, confidence), ...]  confidence = votes / max_votes
    """
    n = len(edge_points)
    if n < 10:
        logger.debug("에지 포인트 부족: %d", n)
        return []

    magnitudes = np.sqrt(grad_dx**2 + grad_dy**2)
    valid_mask = magnitudes > 1e-6
    if not np.any(valid_mask):
        return []

    pts = edge_points[valid_mask]
    dxs = grad_dx[valid_mask] / magnitudes[valid_mask]
    dys = grad_dy[valid_mask] / magnitudes[valid_mask]
    nv = len(pts)

    # 어큐뮬레이터: (bin_cx, bin_cy) → {votes, r_sum}
    accumulator: dict = {}

    for _ in range(max_iter):
        i, j = np.random.choice(nv, 2, replace=False)
        p1, p2 = pts[i], pts[j]

        intersection = _normals_intersection(p1, dxs[i], dys[i], p2, dxs[j], dys[j])
        if intersection is None:
            continue
        cx_c, cy_c = intersection

        r_c = (
            np.sqrt((p1[0] - cx_c)**2 + (p1[1] - cy_c)**2)
            + np.sqrt((p2[0] - cx_c)**2 + (p2[1] - cy_c)**2)
        ) / 2.0

        if not (r_min <= r_c <= r_max):
            continue

        key = (int(round(cx_c / bin_size)), int(round(cy_c / bin_size)))
        if key not in accumulator:
            accumulator[key] = {"votes": 0, "r_sum": 0.0}
        accumulator[key]["votes"] += 1
        accumulator[key]["r_sum"] += r_c

    if not accumulator:
        return []

    peaks = [(k, v) for k, v in accumulator.items() if v["votes"] >= vote_threshold]
    if not peaks:
        logger.debug("투표 임계값(%d) 이상 피크 없음. 최대: %d",
                     vote_threshold, max(v["votes"] for v in accumulator.values()))
        return []

    max_votes = max(v["votes"] for _, v in peaks)
    results: List[Tuple[float, float, float, float]] = []

    for (bcx, bcy), v in sorted(peaks, key=lambda x: x[1]["votes"], reverse=True):
        votes = v["votes"]
        r_avg = v["r_sum"] / votes
        cx_a, cy_a = bcx * bin_size, bcy * bin_size

        # inlier 수집 후 Kasa 정제
        dist_to_circle = np.abs(
            np.sqrt((pts[:, 0] - cx_a)**2 + (pts[:, 1] - cy_a)**2) - r_avg
        )
        inliers = pts[dist_to_circle < bin_size * 2.0]

        refined_cx, refined_cy, refined_r = cx_a, cy_a, r_avg
        if len(inliers) >= 5:
            kasa = _least_squares_circle(inliers)
            if kasa is not None and r_min <= kasa[2] <= r_max:
                refined_cx, refined_cy, refined_r = kasa

        results.append((refined_cx, refined_cy, refined_r, votes / max_votes))

    logger.debug("RHT 피크 %d개 추출", len(results))
    return results


# --- 4. 호 커버리지 ---

def compute_arc_coverage(
    cx: float,
    cy: float,
    r: float,
    edge_points: np.ndarray,
    inlier_threshold: float = 5.0,
) -> float:
    """원 둘레에서 에지 점이 커버하는 각도 비율 (0.0 ~ 1.0)

    10° bin 36개를 사용. inlier 점이 하나라도 있는 bin 비율을 반환.
    부분 호(arc_coverage < 0.5)도 유효로 처리 가능.
    """
    if len(edge_points) == 0 or r <= 0:
        return 0.0

    dists = np.sqrt((edge_points[:, 0] - cx)**2 + (edge_points[:, 1] - cy)**2)
    inliers = edge_points[np.abs(dists - r) < inlier_threshold]
    if len(inliers) == 0:
        return 0.0

    angles_deg = np.degrees(np.arctan2(inliers[:, 1] - cy, inliers[:, 0] - cx)) % 360.0
    num_bins = 36  # 10° 단위
    occupied = np.zeros(num_bins, dtype=bool)
    occupied[(angles_deg / 10).astype(int) % num_bins] = True
    return float(occupied.sum() / num_bins)


# --- 5. Kasa 최소자승 원 피팅 (circle_ransac.py와 동일 패턴) ---

def _least_squares_circle(points: np.ndarray) -> Optional[Tuple[float, float, float]]:
    """Kasa method: x²+y² = 2cx·x + 2cy·y + (r²-cx²-cy²) 선형화"""
    n = len(points)
    if n < 3:
        return None
    x, y = points[:, 0], points[:, 1]
    A = np.column_stack([x, y, np.ones(n)])
    b = x**2 + y**2
    try:
        res, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    cx, cy = res[0] / 2.0, res[1] / 2.0
    r_sq = res[2] + cx**2 + cy**2
    if r_sq <= 0:
        return None
    return (cx, cy, float(np.sqrt(r_sq)))


# --- 6. 중복 제거 (circle_ransac._deduplicate_circles 동일 로직) ---

def _deduplicate_circles(
    circles: List[Tuple[float, float, float, float]],
) -> List[Tuple[float, float, float, float]]:
    """유사한 원 중복 제거 — confidence 높은 쪽 유지.

    중심거리/평균반지름 < 0.2 이고 반지름차/평균반지름 < 0.2 → 중복 판정.
    """
    if not circles:
        return []
    kept: List[Tuple[float, float, float, float]] = []
    for c in sorted(circles, key=lambda c: c[3], reverse=True):
        cx, cy, r, _ = c
        is_dup = False
        for k in kept:
            kcx, kcy, kr, _ = k
            avg_r = (r + kr) / 2.0
            if avg_r < 1:
                continue
            if (np.sqrt((cx - kcx)**2 + (cy - kcy)**2) / avg_r < 0.2
                    and abs(r - kr) / avg_r < 0.2):
                is_dup = True
                break
        if not is_dup:
            kept.append(c)
    return kept


# --- 7. 전체 파이프라인 ---

def detect_circles_rht(
    img_gray: np.ndarray,
    min_arc_coverage: float = 0.25,
) -> List[Tuple[int, int, int]]:
    """RHT 기반 원 검출 통합 파이프라인

    에지+그래디언트 → RHT 투표 → 호 커버리지 필터(≥25%) → 중복 제거

    Args:
        img_gray:         그레이스케일 이미지
        min_arc_coverage: 최소 호 커버리지 (기본 0.25 = 90° 이상)

    Returns:
        [(cx, cy, r), ...] 검출된 원 리스트 (int 좌표)
    """
    edge_points, grad_dx, grad_dy = compute_edge_gradients(img_gray)

    if len(edge_points) == 0:
        logger.warning("에지 포인트 없음 — 원 검출 불가")
        return []

    # 포인트 과다 시 서브샘플링 (속도 최적화)
    max_points = 5000
    if len(edge_points) > max_points:
        idx = np.random.choice(len(edge_points), max_points, replace=False)
        edge_points, grad_dx, grad_dy = edge_points[idx], grad_dx[idx], grad_dy[idx]
        logger.debug("에지 포인트 서브샘플링 → %d", max_points)

    # 이미지 크기 기반 r_min/r_max 동적 설정
    h, w = img_gray.shape[:2]
    img_diag = np.sqrt(h**2 + w**2)
    r_min_auto = max(20, int(img_diag * 0.02))
    r_max_auto = min(int(img_diag * 0.8), 5000)

    candidates = rht_circle_detect(
        edge_points, grad_dx, grad_dy,
        max_iter=15000,
        bin_size=max(5, int(img_diag * 0.002)),
        vote_threshold=3,
        r_min=r_min_auto,
        r_max=r_max_auto,
    )
    if not candidates:
        logger.info("RHT 원 후보 없음")
        return []

    # 호 커버리지 필터
    filtered: List[Tuple[float, float, float, float]] = []
    for cx, cy, r, conf in candidates:
        coverage = compute_arc_coverage(cx, cy, r, edge_points)
        if coverage >= min_arc_coverage:
            filtered.append((cx, cy, r, conf))
            logger.debug("통과 cx=%.1f cy=%.1f r=%.1f coverage=%.2f", cx, cy, r, coverage)
        else:
            logger.debug("제거(커버리지 부족) cx=%.1f cy=%.1f r=%.1f coverage=%.2f",
                         cx, cy, r, coverage)

    deduped = _deduplicate_circles(filtered)
    logger.info("RHT 최종 원 검출: %d개", len(deduped))
    return [(int(round(cx)), int(round(cy)), int(round(r))) for cx, cy, r, _ in deduped]
