"""컨투어 곡률 분해 → 호 그룹핑 → 끊긴 원 복원 모듈

베어링 ASSY 도면에서 클램프·브래킷이 원 윤곽을 끊을 때
기존 findContours 단독으로는 원 피팅이 실패한다.
곡률 분해 → 호 세그먼트 단위 그룹핑으로 완전 원을 복원한다.
참고: circle_ransac.py 의 Kasa _least_squares_circle 패턴 재사용
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _least_squares_circle(points: np.ndarray) -> Optional[Tuple[float, float, float]]:
    """Kasa 최소자승법 원 피팅 — circle_ransac.py 와 동일 패턴"""
    n = len(points)
    if n < 3:
        return None

    x = points[:, 0].astype(np.float64)
    y = points[:, 1].astype(np.float64)

    # x² + y² = 2·cx·x + 2·cy·y + (r² - cx² - cy²)
    A = np.column_stack([x, y, np.ones(n)])
    b = x ** 2 + y ** 2

    try:
        result, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None

    cx = result[0] / 2.0
    cy = result[1] / 2.0
    r_sq = result[2] + cx ** 2 + cy ** 2
    if r_sq <= 0:
        return None

    return (cx, cy, float(np.sqrt(r_sq)))


def _arc_angle(points: np.ndarray, cx: float, cy: float) -> float:
    """호의 중심 커버 각도(degree) 계산"""
    angles = np.degrees(np.arctan2(points[:, 1] - cy, points[:, 0] - cx))
    a_min, a_max = angles.min(), angles.max()
    span = a_max - a_min
    # 360° 경계를 가로지르는 경우 보정
    if span > 180:
        angles_shifted = np.where(angles < 0, angles + 360, angles)
        span = angles_shifted.max() - angles_shifted.min()
    return float(min(span, 360.0))


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def compute_curvature(contour: np.ndarray, window: int = 7) -> np.ndarray:
    """컨투어 각 점의 곡률 계산 (슬라이딩 윈도우)

    공식: k = |x'y'' - y'x''| / (x'² + y'²)^(3/2)
    numpy.gradient 로 1·2차 도함수를 추정한다.

    Args:
        contour: (N, 1, 2) 또는 (N, 2) OpenCV 컨투어
        window: 스무딩 윈도우 크기 (홀수 권장)

    Returns:
        (N,) 곡률 배열 (단위: 1/px)
    """
    pts = contour.reshape(-1, 2).astype(np.float64)
    n = len(pts)

    if n < window:
        return np.zeros(n)

    # 슬라이딩 평균으로 노이즈 억제
    half = window // 2
    smoothed = np.zeros_like(pts)
    for i in range(n):
        idxs = [(i + k - half) % n for k in range(window)]
        smoothed[i] = pts[idxs].mean(axis=0)

    x = smoothed[:, 0]
    y = smoothed[:, 1]

    # 1차 도함수
    dx = np.gradient(x)
    dy = np.gradient(y)

    # 2차 도함수
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)

    # 분모가 0에 가까우면 곡률 0으로 처리
    denom = (dx ** 2 + dy ** 2) ** 1.5
    with np.errstate(invalid='ignore', divide='ignore'):
        k = np.where(denom > 1e-8, np.abs(dx * ddy - dy * ddx) / denom, 0.0)

    return k


def decompose_contour(
    contour: np.ndarray,
    curvature_threshold: float = 0.005,
    min_segment_len: int = 10,
) -> List[dict]:
    """컨투어를 호·직선 세그먼트로 분해

    1. 곡률을 계산한다.
    2. 곡률이 급격히 변하는 점(변곡점)에서 세그먼트를 분할한다.
    3. 세그먼트 평균 곡률 > threshold → 호(arc), 나머지 → 직선(line).
    4. 호 세그먼트에는 Kasa 원 피팅을 수행한다.

    Args:
        contour: (N, 1, 2) 또는 (N, 2) 컨투어
        curvature_threshold: 호 판정 평균 곡률 하한
        min_segment_len: 이 길이 미만 세그먼트는 무시

    Returns:
        세그먼트 dict 리스트.
        - arc: {type, cx, cy, r, points, arc_angle}
        - line: {type, start, end, length}
    """
    pts = contour.reshape(-1, 2).astype(np.float64)
    n = len(pts)
    if n < min_segment_len:
        return []

    k = compute_curvature(pts)

    # 변곡점: 곡률의 2차 미분이 큰 지점 (변화율이 큰 곳)
    dk = np.abs(np.gradient(k))
    # 상위 5% 를 변곡점 후보로 사용
    dk_thresh = np.percentile(dk, 95)
    split_mask = dk > dk_thresh

    # 연속 True 블록의 대표 인덱스만 유지
    split_indices = []
    in_block = False
    block_start = 0
    for i in range(n):
        if split_mask[i] and not in_block:
            in_block = True
            block_start = i
        elif not split_mask[i] and in_block:
            in_block = False
            split_indices.append((block_start + i) // 2)
    if in_block:
        split_indices.append((block_start + n) // 2)

    # 세그먼트 경계 인덱스 구성
    boundaries = sorted(set([0] + split_indices + [n]))

    segments = []
    for si in range(len(boundaries) - 1):
        s, e = boundaries[si], boundaries[si + 1]
        seg_pts = pts[s:e]
        if len(seg_pts) < min_segment_len:
            continue

        avg_k = float(k[s:e].mean())

        if avg_k > curvature_threshold:
            # 호 세그먼트: Kasa 원 피팅
            fit = _least_squares_circle(seg_pts)
            if fit is None:
                continue
            cx, cy, r = fit
            # 반지름 유효성: 너무 작거나 비현실적으로 큰 것은 제외
            if r < 3 or r > 5000:
                continue
            angle = _arc_angle(seg_pts, cx, cy)
            segments.append({
                "type": "arc",
                "cx": cx,
                "cy": cy,
                "r": r,
                "points": seg_pts,
                "arc_angle": angle,
            })
        else:
            # 직선 세그먼트
            start = tuple(seg_pts[0].astype(int))
            end = tuple(seg_pts[-1].astype(int))
            length = float(np.linalg.norm(seg_pts[-1] - seg_pts[0]))
            segments.append({
                "type": "line",
                "start": start,
                "end": end,
                "length": length,
            })

    return segments


def group_arcs_by_circle(
    arc_segments: List[dict],
    center_tol: float = 0.15,
    radius_tol: float = 0.10,
) -> List[dict]:
    """유사 호를 동일 원으로 그룹핑하여 원 복원

    모든 호 쌍에 대해 (중심 거리 / avg_r, 반지름 차 / avg_r) 를 계산하고
    임계값 이내인 호를 greedy merge 한다.
    그룹 포인트 전체로 Kasa 최종 원 피팅을 수행한다.

    Args:
        arc_segments: decompose_contour 에서 type='arc' 인 세그먼트 리스트
        center_tol: 중심 거리 허용 비율 (avg_r 대비)
        radius_tol: 반지름 차 허용 비율 (avg_r 대비)

    Returns:
        [{cx, cy, r, arc_coverage, confidence, n_arcs}, ...]
    """
    arcs = [s for s in arc_segments if s.get("type") == "arc"]
    if not arcs:
        return []

    n = len(arcs)
    used = [False] * n
    groups: List[List[int]] = []

    for i in range(n):
        if used[i]:
            continue
        group = [i]
        used[i] = True
        for j in range(i + 1, n):
            if used[j]:
                continue
            a, b = arcs[i], arcs[j]
            avg_r = (a["r"] + b["r"]) / 2.0
            if avg_r < 1:
                continue
            center_dist = np.hypot(a["cx"] - b["cx"], a["cy"] - b["cy"])
            r_diff = abs(a["r"] - b["r"])
            if center_dist / avg_r < center_tol and r_diff / avg_r < radius_tol:
                group.append(j)
                used[j] = True
        groups.append(group)

    results = []
    for group in groups:
        group_arcs = [arcs[i] for i in group]
        all_pts = np.vstack([a["points"] for a in group_arcs])

        fit = _least_squares_circle(all_pts)
        if fit is None:
            continue
        cx, cy, r = fit
        if r < 3 or r > 5000:
            continue

        # 커버 각도 합산 (최대 360°)
        total_angle = min(360.0, sum(a["arc_angle"] for a in group_arcs))
        arc_coverage = total_angle / 360.0

        # 피팅 잔차 기반 confidence
        dists = np.abs(np.sqrt((all_pts[:, 0] - cx) ** 2 + (all_pts[:, 1] - cy) ** 2) - r)
        inlier_ratio = float(np.mean(dists < max(2.0, r * 0.05)))
        confidence = min(1.0, inlier_ratio * (1.0 + 0.1 * (len(group) - 1)))

        results.append({
            "cx": cx,
            "cy": cy,
            "r": r,
            "arc_coverage": arc_coverage,
            "confidence": confidence,
            "n_arcs": len(group),
        })

    # confidence 내림차순 정렬
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results


def detect_circles_decomposition(
    img_gray: np.ndarray,
    min_contour_len: int = 30,
    min_arc_coverage: float = 0.20,
) -> List[Tuple[int, int, int]]:
    """곡률 분해 기반 원 검출 통합 파이프라인

    1. Canny 에지 검출
    2. findContours 로 컨투어 추출
    3. 각 컨투어를 호·직선 세그먼트로 분해
    4. 호 세그먼트를 그룹핑하여 끊긴 원 복원
    5. arc_coverage 임계값 이상만 반환

    Args:
        img_gray: 그레이스케일 입력 이미지
        min_contour_len: 처리할 최소 컨투어 포인트 수
        min_arc_coverage: 반환할 최소 호 커버 비율 (0~1)

    Returns:
        [(cx, cy, r), ...] 검출된 원 리스트
    """
    blurred = cv2.GaussianBlur(img_gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 30, 100)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    logger.debug("컨투어 수: %d", len(contours))

    # 이미지 크기 기반 최소 반지름
    h, w = img_gray.shape[:2]
    img_diag = np.sqrt(h**2 + w**2)
    r_min_filter = max(50, img_diag * 0.02)

    # 모든 컨투어에서 호 세그먼트 수집
    all_arcs: List[dict] = []
    for cnt in contours:
        if len(cnt) < min_contour_len:
            continue
        segments = decompose_contour(cnt, curvature_threshold=0.008, min_segment_len=20)
        all_arcs.extend(
            s for s in segments
            if s["type"] == "arc" and s["r"] >= r_min_filter and s["arc_angle"] >= 15.0
        )

    logger.debug("호 세그먼트 수: %d", len(all_arcs))

    # 호 그룹핑으로 원 복원
    circle_groups = group_arcs_by_circle(all_arcs)

    # arc_coverage 필터링 + 중복 제거
    results: List[Tuple[int, int, int]] = []
    seen: List[Tuple[float, float, float]] = []

    for g in circle_groups:
        if g["arc_coverage"] < min_arc_coverage:
            continue
        cx, cy, r = g["cx"], g["cy"], g["r"]
        # 이미 유사한 원이 있으면 스킵
        dup = False
        for scx, scy, sr in seen:
            avg_r = (r + sr) / 2.0
            if avg_r < 1:
                continue
            if np.hypot(cx - scx, cy - scy) / avg_r < 0.15 and abs(r - sr) / avg_r < 0.15:
                dup = True
                break
        if not dup:
            seen.append((cx, cy, r))
            results.append((int(round(cx)), int(round(cy)), int(round(r))))

    logger.debug("최종 검출 원 수: %d", len(results))
    return results
