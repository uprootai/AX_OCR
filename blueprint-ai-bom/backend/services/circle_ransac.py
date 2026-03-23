"""RANSAC 원 피팅 + 호(arc) 클러스터링 모듈

베어링 ASSY 도면에서 부착 부품(클램프, 브래킷)이 원 윤곽을 끊는 경우,
기존 Contour/HoughCircles로는 원 검출이 부정확하다.

- ransac_circle_fit: 에지 포인트에서 RANSAC으로 원 파라미터 추정
- cluster_arcs_to_circles: 불완전 호를 병합하여 완전 원 후보 생성
- detect_circles_ransac: 위 두 함수를 조합한 통합 파이프라인
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def ransac_circle_fit(
    points: np.ndarray,
    max_iterations: int = 200,
    inlier_threshold: float = 3.0,
    min_inlier_ratio: float = 0.3,
) -> Optional[Tuple[float, float, float, float]]:
    """RANSAC으로 2D 점들에서 원 파라미터(cx, cy, r) 추정

    Args:
        points: (N, 2) 에지 포인트 배열
        max_iterations: RANSAC 반복 횟수
        inlier_threshold: inlier 판정 거리(px)
        min_inlier_ratio: 최소 inlier 비율 (이하면 실패)

    Returns:
        (cx, cy, r, inlier_ratio) 또는 None (실패 시)
    """
    if points.shape[0] < 10:
        return None

    n = points.shape[0]
    best_cx, best_cy, best_r = 0.0, 0.0, 0.0
    best_inlier_count = 0

    pts = points.astype(np.float64)

    for _ in range(max_iterations):
        # 3점 무작위 샘플
        idx = np.random.choice(n, 3, replace=False)
        p1, p2, p3 = pts[idx[0]], pts[idx[1]], pts[idx[2]]

        # 3점으로 원 중심/반지름 계산 (외접원)
        result = _circle_from_three_points(p1, p2, p3)
        if result is None:
            continue
        cx, cy, r = result

        # 반지름 유효성 체크 (너무 작거나 크면 스킵)
        if r < 5 or r > 5000:
            continue

        # inlier 계산: 각 점에서 원까지 거리
        dists = np.abs(np.sqrt((pts[:, 0] - cx)**2 + (pts[:, 1] - cy)**2) - r)
        inlier_count = np.sum(dists < inlier_threshold)

        if inlier_count > best_inlier_count:
            best_inlier_count = inlier_count
            best_cx, best_cy, best_r = cx, cy, r

    inlier_ratio = best_inlier_count / n
    if inlier_ratio < min_inlier_ratio:
        return None

    # inlier로 최종 원 파라미터 정제 (최소자승)
    dists = np.abs(np.sqrt((pts[:, 0] - best_cx)**2 + (pts[:, 1] - best_cy)**2) - best_r)
    inliers = pts[dists < inlier_threshold]
    if len(inliers) >= 10:
        refined = _least_squares_circle(inliers)
        if refined is not None:
            best_cx, best_cy, best_r = refined

    return (best_cx, best_cy, best_r, inlier_ratio)


def _circle_from_three_points(
    p1: np.ndarray, p2: np.ndarray, p3: np.ndarray,
) -> Optional[Tuple[float, float, float]]:
    """3점의 외접원 계산 — 공선이면 None"""
    ax, ay = p1[0], p1[1]
    bx, by = p2[0], p2[1]
    cx, cy = p3[0], p3[1]

    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-10:
        return None  # 공선

    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    r = np.sqrt((ax - ux)**2 + (ay - uy)**2)

    return (ux, uy, r)


def _least_squares_circle(points: np.ndarray) -> Optional[Tuple[float, float, float]]:
    """최소자승법 원 피팅 (Kasa method)

    A @ [cx, cy, c]^T = b 형태로 풀어 원 중심과 반지름 추정.
    """
    n = len(points)
    if n < 3:
        return None

    x = points[:, 0]
    y = points[:, 1]

    # Kasa: x^2 + y^2 = 2*cx*x + 2*cy*y + (r^2 - cx^2 - cy^2)
    A = np.column_stack([x, y, np.ones(n)])
    b = x**2 + y**2

    try:
        result, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None

    cx = result[0] / 2.0
    cy = result[1] / 2.0
    r_sq = result[2] + cx**2 + cy**2
    if r_sq <= 0:
        return None

    return (cx, cy, np.sqrt(r_sq))


def cluster_arcs_to_circles(
    contours: list,
    img_w: int,
    img_h: int,
    distance_threshold: float = 0.15,
    min_arc_points: int = 15,
) -> List[Tuple[float, float, float, float]]:
    """불완전 호(arc)를 클러스터링하여 동일 원에 속하는 호 병합

    각 컨투어를 타원 피팅하여 원 후보를 생성하고,
    중심/반지름이 유사한 호를 병합하여 RANSAC으로 정제.

    Args:
        contours: cv2.findContours 결과
        img_w, img_h: 이미지 크기
        distance_threshold: 중심 거리 유사도 비율 (반지름 대비)
        min_arc_points: 최소 호 포인트 수

    Returns:
        [(cx, cy, r, confidence), ...] 병합된 원 후보 리스트
    """
    # 1단계: 각 컨투어를 호 후보로 변환
    arc_candidates = []
    for cnt in contours:
        if len(cnt) < min_arc_points:
            continue
        # 타원 피팅으로 대략적 원 추정
        if len(cnt) < 5:
            continue
        try:
            ellipse = cv2.fitEllipse(cnt)
        except cv2.error:
            continue
        (ecx, ecy), (ma, MA), _ = ellipse
        if max(ma, MA) == 0:
            continue
        aspect = min(ma, MA) / max(ma, MA)
        # 원형에 가까운 것만 (타원 제외)
        if aspect < 0.5:
            continue
        r_est = (ma + MA) / 4.0
        if r_est < 5 or r_est > min(img_w, img_h) * 0.45:
            continue
        arc_candidates.append({
            "cx": ecx, "cy": ecy, "r": r_est,
            "points": cnt.reshape(-1, 2),
            "aspect": aspect,
        })

    if not arc_candidates:
        return []

    # 2단계: 유사 원 클러스터링 (greedy merge)
    used = [False] * len(arc_candidates)
    clusters: List[List[int]] = []

    for i, a in enumerate(arc_candidates):
        if used[i]:
            continue
        cluster = [i]
        used[i] = True
        for j in range(i + 1, len(arc_candidates)):
            if used[j]:
                continue
            b = arc_candidates[j]
            # 중심 거리와 반지름 차이로 유사도 판정
            center_dist = np.sqrt((a["cx"] - b["cx"])**2 + (a["cy"] - b["cy"])**2)
            avg_r = (a["r"] + b["r"]) / 2.0
            if avg_r < 1:
                continue
            if center_dist / avg_r < distance_threshold and abs(a["r"] - b["r"]) / avg_r < 0.25:
                cluster.append(j)
                used[j] = True
        clusters.append(cluster)

    # 3단계: 각 클러스터의 포인트를 병합하여 RANSAC 정제
    results = []
    for cluster in clusters:
        all_points = np.vstack([arc_candidates[i]["points"] for i in cluster])
        if len(all_points) < 15:
            continue

        fit = ransac_circle_fit(
            all_points,
            max_iterations=150,
            inlier_threshold=4.0,
            min_inlier_ratio=0.2,
        )
        if fit is not None:
            cx, cy, r, conf = fit
            # 클러스터 크기에 따라 confidence 보정
            arc_count = len(cluster)
            total_pts = len(all_points)
            conf_adjusted = min(1.0, conf * (1.0 + 0.1 * (arc_count - 1)))
            results.append((cx, cy, r, conf_adjusted))

    return results


def detect_circles_ransac(
    img_gray: np.ndarray,
) -> List[Tuple[int, int, int]]:
    """RANSAC 기반 원 검출 통합 파이프라인

    1. Canny 에지 검출
    2. 컨투어 추출
    3. 호 클러스터링으로 불완전 원 복원
    4. 전체 에지 포인트에서 RANSAC 원 피팅 (보조)

    Returns:
        [(cx, cy, r), ...] 검출된 원 리스트
    """
    h, w = img_gray.shape[:2]
    blurred = cv2.GaussianBlur(img_gray, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # 호 클러스터링
    arc_results = cluster_arcs_to_circles(contours, w, h)

    # 중복 제거: 중심/반지름이 유사한 원 통합
    merged = _deduplicate_circles(arc_results, w, h)

    return [(int(cx), int(cy), int(r)) for cx, cy, r, _ in merged]


def _deduplicate_circles(
    circles: List[Tuple[float, float, float, float]],
    img_w: int,
    img_h: int,
) -> List[Tuple[float, float, float, float]]:
    """유사한 원 중복 제거 — confidence 높은 쪽 유지"""
    if not circles:
        return []

    # confidence 내림차순 정렬
    sorted_circles = sorted(circles, key=lambda c: c[3], reverse=True)
    kept = []

    for c in sorted_circles:
        cx, cy, r, conf = c
        is_dup = False
        for k in kept:
            kcx, kcy, kr, _ = k
            center_dist = np.sqrt((cx - kcx)**2 + (cy - kcy)**2)
            avg_r = (r + kr) / 2.0
            if avg_r < 1:
                continue
            if center_dist / avg_r < 0.2 and abs(r - kr) / avg_r < 0.2:
                is_dup = True
                break
        if not is_dup:
            kept.append(c)

    return kept


def ensemble_circles(
    existing: List[Tuple[int, int, int]],
    ransac: List[Tuple[int, int, int]],
    preference: str = "union",
) -> List[Tuple[int, int, int]]:
    """기존 결과와 RANSAC 결과를 앙상블

    Args:
        existing: 기존 Contour/Hough 결과
        ransac: RANSAC 결과
        preference: "union" (합집합, 중복 제거) 또는 "ransac_priority" (RANSAC 우선)

    Returns:
        앙상블된 원 리스트
    """
    if not ransac:
        return existing
    if not existing:
        return ransac

    # 합집합 + 중복 제거
    all_circles = [(float(cx), float(cy), float(r), 0.5) for cx, cy, r in existing]
    all_circles += [(float(cx), float(cy), float(r), 0.6) for cx, cy, r in ransac]

    # 이미지 크기를 최대 반지름에서 추정
    max_r = max(r for _, _, r, _ in all_circles) if all_circles else 100
    img_est = int(max_r * 10)

    deduped = _deduplicate_circles(all_circles, img_est, img_est)
    return [(int(cx), int(cy), int(r)) for cx, cy, r, _ in deduped]
