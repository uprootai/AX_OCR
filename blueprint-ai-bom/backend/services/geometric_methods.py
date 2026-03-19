"""기하학 기반 R vs Ø 판별 방법 3종

Method L: endpoint_topology — 치수선 끝점이 원 중심/원주에 닿는지로 판별
Method M: symbol_search — OCR 텍스트에서 R/Ø 접두사로 판별
Method N: center_raycast — 원 중심에서 8방향 ray 발사, 치수와 교차 거리로 판별
"""
import cv2
import re
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple

from schemas.dimension import (
    Dimension, DimensionType, MaterialRole,
    GeometryDebugInfo, CircleInfo, DimLineInfo, RoiInfo, RayCastInfo,
)

logger = logging.getLogger(__name__)


def _detect_circles_for_methods(img_gray: np.ndarray) -> List[Tuple[int, int, int]]:
    """컨투어+타원피팅으로 원 검출, 실패 시 HoughCircles 폴백

    기계 도면의 해칭/치수선 간섭에 강한 컨투어 기반 접근을 우선 사용.
    """
    h, w = img_gray.shape[:2]
    max_dim = 2000
    scale = 1.0
    img = img_gray.copy()
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    rh, rw = img.shape[:2]

    # 1차: 컨투어 기반
    circles = _contour_circle_detect(img, rw, rh, scale)
    if circles:
        return circles

    # 2차: HoughCircles 폴백
    return _hough_circle_detect(img, rw, rh, scale)


def _contour_circle_detect(
    img: np.ndarray, rw: int, rh: int, scale: float
) -> List[Tuple[int, int, int]]:
    """Canny → 컨투어 → 타원 피팅 → 원형 후보 반환"""
    blurred = cv2.GaussianBlur(img, (5, 5), 1.5)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    min_area = rw * rh * 0.002
    max_radius = min(rw, rh) * 0.45  # 도면 전체 윤곽 제외
    results = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or len(cnt) < 20:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        if min(bw, bh) / max(bw, bh) < 0.6:
            continue
        ellipse = cv2.fitEllipse(cnt)
        (cx, cy), (ma, MA), _ = ellipse
        if max(ma, MA) == 0 or min(ma, MA) / max(ma, MA) < 0.6:
            continue
        r_scaled = (ma + MA) / 4
        if r_scaled > max_radius:
            continue
        r = int(r_scaled / scale)
        results.append((int(cx / scale), int(cy / scale), r))

    return results


def _hough_circle_detect(
    img: np.ndarray, rw: int, rh: int, scale: float
) -> List[Tuple[int, int, int]]:
    """HoughCircles 폴백"""
    blurred = cv2.GaussianBlur(img, (9, 9), 2)
    min_r = min(rw, rh) // 20
    max_r = min(rw, rh) // 3

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=1.2, minDist=min_r,
        param1=100, param2=50,
        minRadius=min_r, maxRadius=max_r,
    )
    if circles is None:
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT,
            dp=1.5, minDist=min_r // 2,
            param1=80, param2=30,
            minRadius=min_r // 2, maxRadius=max_r,
        )
    if circles is None:
        return []

    arr = np.round(circles[0]).astype(int)
    if scale != 1.0:
        arr = np.round(arr / scale).astype(int)
    return [(int(c[0]), int(c[1]), int(c[2])) for c in arr]


def _detect_lines_lsd(img_gray: np.ndarray) -> List[Tuple[float, float, float, float, float]]:
    """LSD로 직선 검출 → (x1, y1, x2, y2, length)"""
    lsd = cv2.createLineSegmentDetector(0)
    lines, _, _, _ = lsd.detect(img_gray)
    if lines is None:
        return []

    result = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if length >= 30:
            result.append((float(x1), float(y1), float(x2), float(y2), float(length)))
    return result


def _parse_numeric(text: str) -> Optional[float]:
    """치수 텍스트에서 숫자값 추출"""
    m = re.search(r'(\d+\.?\d*)', re.sub(r'^[ØφΦ⌀RrMmCc]', '', text.strip()))
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _value_ranking_fallback(dims: List[Dimension]) -> List[Dimension]:
    """미분류 치수에 값 크기 기반 폴백 적용 (L/M/N 공통)

    기하학 분석으로 분류하지 못한 경우, 값 크기 순으로 OD/ID/W 배정.
    """
    result = list(dims)
    # 이미 분류된 역할 확인
    has_od = any(d.material_role == MaterialRole.OUTER_DIAMETER for d in result)
    has_id = any(d.material_role == MaterialRole.INNER_DIAMETER for d in result)
    has_w = any(d.material_role == MaterialRole.LENGTH for d in result)

    if has_od and has_id and has_w:
        return result

    # 미분류 치수 중 숫자값이 있는 것만 수집
    unclassified = []
    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        v = _parse_numeric(d.value)
        if v is not None and v > 5:
            # 나사산, 각도 제외
            text = d.value.strip()
            if re.match(r'^M\d', text, re.IGNORECASE):
                continue
            if re.search(r'°|deg', text, re.IGNORECASE):
                continue
            unclassified.append((i, v))

    unclassified.sort(key=lambda x: x[1], reverse=True)

    for idx, (i, v) in enumerate(unclassified):
        if idx == 0 and not has_od:
            result[i] = result[i].model_copy(update={"material_role": MaterialRole.OUTER_DIAMETER})
            has_od = True
        elif idx == 1 and not has_id:
            result[i] = result[i].model_copy(update={"material_role": MaterialRole.INNER_DIAMETER})
            has_id = True
        elif idx == 2 and not has_w:
            result[i] = result[i].model_copy(update={"material_role": MaterialRole.LENGTH})
            has_w = True

    return result


# ==================== Method L: Endpoint Topology ====================

def endpoint_topology_classify(
    dimensions: List[Dimension],
    image_path: str,
    image_width: int,
    image_height: int,
) -> Tuple[List[Dimension], GeometryDebugInfo]:
    """치수선 끝점 토폴로지로 RADIUS vs DIAMETER 판별

    끝점이 원 중심 근처 → RADIUS → value×2
    양 끝점 모두 원주 근처 → DIAMETER
    """
    debug = GeometryDebugInfo()
    result = list(dimensions)

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return result, debug

    circles = _detect_circles_for_methods(img)
    if not circles:
        return result, debug

    # 가장 큰 원
    circles.sort(key=lambda c: c[2], reverse=True)
    outer = circles[0]
    cx, cy, r_outer = outer

    debug.circles = [
        CircleInfo(cx=c[0], cy=c[1], radius=c[2], confidence=0.5)
        for c in circles[:5]
    ]

    lines = _detect_lines_lsd(img)

    # 원 근처 치수선 필터
    dim_lines_info = []
    for x1, y1, x2, y2, length in lines:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dist = np.sqrt((mx - cx)**2 + (my - cy)**2)
        if dist < r_outer * 0.5 or dist > r_outer * 3.5:
            continue

        # 끝점의 원 중심/원주 근접도 판별
        ep_types = []
        for px, py in [(x1, y1), (x2, y2)]:
            d_center = np.sqrt((px - cx)**2 + (py - cy)**2)
            d_circumference = abs(d_center - r_outer)
            if d_center < r_outer * 0.15:
                ep_types.append("center")
            elif d_circumference < r_outer * 0.2:
                ep_types.append("circumference")
            else:
                ep_types.append("unknown")

        near_center = "center" in ep_types
        ep_type = "center" if near_center else ("circumference" if ep_types.count("circumference") == 2 else "unknown")

        dim_lines_info.append({
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "near_center": near_center, "endpoint_type": ep_type,
        })

    debug.dim_lines = [
        DimLineInfo(**dl) for dl in dim_lines_info[:20]
    ]

    # 치수와 치수선 매칭 → 역할 결정
    for i, d in enumerate(result):
        if d.material_role is not None:
            continue
        v = _parse_numeric(d.value)
        if v is None or v < 5:
            continue

        dim_cx = (d.bbox.x1 + d.bbox.x2) / 2
        dim_cy = (d.bbox.y1 + d.bbox.y2) / 2

        # 가장 가까운 치수선 찾기
        best_dl = None
        best_dist = float('inf')
        for dl in dim_lines_info:
            for px, py in [(dl["x1"], dl["y1"]), (dl["x2"], dl["y2"])]:
                dd = np.sqrt((px - dim_cx)**2 + (py - dim_cy)**2)
                if dd < best_dist:
                    best_dist = dd
                    best_dl = dl

        if best_dl and best_dist < r_outer * 0.5:
            if best_dl["near_center"]:
                # RADIUS → 직경 변환
                dia_val = v * 2
                dia_str = str(int(dia_val)) if dia_val == int(dia_val) else f"{dia_val:.1f}"
                result[i] = d.model_copy(update={
                    "value": f"Ø{dia_str}",
                    "dimension_type": DimensionType.DIAMETER,
                    "material_role": MaterialRole.OUTER_DIAMETER if dia_val > 80 else MaterialRole.INNER_DIAMETER,
                })
            elif best_dl["endpoint_type"] == "circumference":
                result[i] = d.model_copy(update={
                    "material_role": MaterialRole.OUTER_DIAMETER if v > 80 else MaterialRole.INNER_DIAMETER,
                })

    result = _value_ranking_fallback(result)
    return result, debug


# ==================== Method M: Symbol Search ====================

def symbol_search_classify(
    dimensions: List[Dimension],
) -> Tuple[List[Dimension], GeometryDebugInfo]:
    """OCR 텍스트의 R/Ø 심볼 접두사로 판별

    R + 숫자 → RADIUS → value×2
    Ø + 숫자 → DIAMETER
    """
    debug = GeometryDebugInfo()
    result = list(dimensions)
    symbols = []

    r_pattern = re.compile(r'^[Rr]\s*(\d+[\.,]?\d*)')
    d_pattern = re.compile(r'^[Øø⌀∅ΦφΦ]\s*(\d+[\.,]?\d*)')

    for i, d in enumerate(result):
        text = d.value.strip()
        bbox_cx = (d.bbox.x1 + d.bbox.x2) / 2
        bbox_cy = (d.bbox.y1 + d.bbox.y2) / 2

        r_match = r_pattern.match(text)
        d_match = d_pattern.match(text)

        if r_match:
            r_val = float(r_match.group(1).replace(',', '.'))
            dia_val = r_val * 2
            dia_str = str(int(dia_val)) if dia_val == int(dia_val) else f"{dia_val:.1f}"
            symbols.append({
                "text": text, "x": bbox_cx, "y": bbox_cy,
                "type": "RADIUS", "original": r_val, "converted": dia_val,
            })
            if d.material_role is None and r_val >= 5:
                result[i] = d.model_copy(update={
                    "value": f"Ø{dia_str}",
                    "dimension_type": DimensionType.DIAMETER,
                    "material_role": MaterialRole.OUTER_DIAMETER if dia_val > 80 else MaterialRole.INNER_DIAMETER,
                })
        elif d_match:
            d_val = float(d_match.group(1).replace(',', '.'))
            symbols.append({
                "text": text, "x": bbox_cx, "y": bbox_cy,
                "type": "DIAMETER", "value": d_val,
            })
            if d.material_role is None and d_val >= 5:
                result[i] = d.model_copy(update={
                    "material_role": MaterialRole.OUTER_DIAMETER if d_val > 80 else MaterialRole.INNER_DIAMETER,
                })

    debug.symbols_found = symbols
    result = _value_ranking_fallback(result)
    return result, debug


# ==================== Method N: Center Raycast ====================

def center_raycast_classify(
    dimensions: List[Dimension],
    image_path: str,
    image_width: int,
    image_height: int,
) -> Tuple[List[Dimension], GeometryDebugInfo]:
    """원 중심에서 8방향 ray 발사 → 치수와 교차 거리로 판별

    교차 거리 ≈ 반지름 → RADIUS 후보 → value×2
    교차 거리 ≈ 직경 → DIAMETER 후보
    """
    debug = GeometryDebugInfo()
    result = list(dimensions)

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return result, debug

    circles = _detect_circles_for_methods(img)
    if not circles:
        return result, debug

    circles.sort(key=lambda c: c[2], reverse=True)
    outer = circles[0]
    cx, cy, r_outer = outer

    debug.circles = [
        CircleInfo(cx=c[0], cy=c[1], radius=c[2], confidence=0.5)
        for c in circles[:5]
    ]

    # 8방향 ray (N, NE, E, SE, S, SW, W, NW)
    angles = [0, 45, 90, 135, 180, 225, 270, 315]
    ray_length = r_outer * 3
    rays_info = []

    for angle in angles:
        rad = np.radians(angle)
        end_x = cx + ray_length * np.cos(rad)
        end_y = cy - ray_length * np.sin(rad)  # y축 반전 (이미지 좌표)

        # 각 치수 bbox와 ray 교차 확인
        for i, d in enumerate(result):
            bx1, by1, bx2, by2 = d.bbox.x1, d.bbox.y1, d.bbox.x2, d.bbox.y2
            # ray와 bbox 교차 간이 검사
            hit_x, hit_y = _ray_bbox_intersection(cx, cy, end_x, end_y, bx1, by1, bx2, by2)
            if hit_x is not None:
                distance = np.sqrt((hit_x - cx)**2 + (hit_y - cy)**2)
                rays_info.append({
                    "origin_cx": float(cx), "origin_cy": float(cy),
                    "angle_deg": float(angle),
                    "hit_x": float(hit_x), "hit_y": float(hit_y),
                    "distance": float(distance),
                    "dim_idx": i,
                })

    debug.rays = [RayCastInfo(**{k: v for k, v in r.items() if k != "dim_idx"}) for r in rays_info[:32]]

    # ray 교차한 치수 분석
    for ray in rays_info:
        i = ray["dim_idx"]
        d = result[i]
        if d.material_role is not None:
            continue

        v = _parse_numeric(d.value)
        if v is None or v < 5:
            continue

        distance = ray["distance"]
        # 거리와 반지름 비교
        r_ratio = distance / r_outer if r_outer > 0 else 0

        if 0.7 <= r_ratio <= 1.3:
            # 거리 ≈ 반지름 → RADIUS 후보, 직경으로 변환
            if d.dimension_type == DimensionType.RADIUS or d.value.strip().upper().startswith('R'):
                dia_val = v * 2
                dia_str = str(int(dia_val)) if dia_val == int(dia_val) else f"{dia_val:.1f}"
                result[i] = d.model_copy(update={
                    "value": f"Ø{dia_str}",
                    "dimension_type": DimensionType.DIAMETER,
                    "material_role": MaterialRole.OUTER_DIAMETER if dia_val > 80 else MaterialRole.INNER_DIAMETER,
                })
            else:
                result[i] = d.model_copy(update={
                    "material_role": MaterialRole.OUTER_DIAMETER if v > 80 else MaterialRole.INNER_DIAMETER,
                })

    result = _value_ranking_fallback(result)
    return result, debug


def _ray_bbox_intersection(
    ox: float, oy: float, ex: float, ey: float,
    bx1: float, by1: float, bx2: float, by2: float,
) -> Tuple[Optional[float], Optional[float]]:
    """간이 ray-bbox 교차 검사 — ray가 bbox를 관통하면 중점 반환"""
    # bbox 중점이 ray 방향에 있는지 확인
    bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
    dx, dy = ex - ox, ey - oy
    length = np.sqrt(dx**2 + dy**2)
    if length < 1:
        return None, None

    # ray 위의 가장 가까운 점
    t = max(0, min(1, ((bcx - ox) * dx + (bcy - oy) * dy) / (length**2)))
    closest_x = ox + t * dx
    closest_y = oy + t * dy

    # bbox 내부인지 확인 (패딩 포함)
    pad = max(bx2 - bx1, by2 - by1) * 0.3
    if (bx1 - pad <= closest_x <= bx2 + pad and
            by1 - pad <= closest_y <= by2 + pad):
        return bcx, bcy

    return None, None
