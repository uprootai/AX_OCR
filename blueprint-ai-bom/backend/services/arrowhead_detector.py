"""화살촉 검출 기반 치수 매핑 모듈

기계/베어링 도면에서 화살촉(▶ ◀)을 Black Hat 모폴로지로 검출하여
치수선 → 텍스트를 직접 매핑하고 OD/ID/W를 분류한다.
"""
import re
import cv2
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Step 1: 화살촉 검출 ──────────────────────────────────────

def detect_arrowheads(img_gray: np.ndarray) -> List[Dict]:
    """Black Hat(closing - original) 모폴로지로 실선 삼각형 화살촉 검출

    Args:
        img_gray: 그레이스케일 도면 이미지
    Returns:
        [{x, y, angle, bbox:{x1,y1,x2,y2}, area}, ...]
        angle: PCA 주축 방향(도, 0°=오른쪽)
    """
    if img_gray is None or img_gray.size == 0:
        logger.warning("detect_arrowheads: 빈 이미지 입력")
        return []

    _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 커널 크기: 이미지 단변 / 150, 최소 3, 홀수 보장
    ks = max(3, min(img_gray.shape[0], img_gray.shape[1]) // 150)
    ks = ks if ks % 2 == 1 else ks + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    black_hat = cv2.subtract(cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel), binary)

    # 끊어진 화살촉 연결
    dil_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    black_hat = cv2.dilate(black_hat, dil_k, iterations=1)

    contours, _ = cv2.findContours(black_hat, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    arrowheads = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50 or area > 500:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0 or w == 0:
            continue
        aspect = w / h
        if aspect < 0.3 or aspect > 3.0:
            continue
        M = cv2.moments(cnt)
        if M["m00"] < 1e-6:
            cx, cy = x + w // 2, y + h // 2
        else:
            cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
        arrowheads.append({
            "x": cx, "y": cy,
            "angle": _contour_angle(cnt),
            "bbox": {"x1": x, "y1": y, "x2": x + w, "y2": y + h},
            "area": float(area),
        })

    logger.info(f"화살촉 검출: {len(arrowheads)}개 (커널={ks})")
    return arrowheads


def _contour_angle(cnt: np.ndarray) -> float:
    """PCA 주축 방향 (도, -90~90)"""
    pts = cnt.reshape(-1, 2).astype(np.float32)
    if len(pts) < 3:
        return 0.0
    centered = pts - pts.mean(axis=0)
    cov = np.dot(centered.T, centered) / len(pts)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    principal = eigenvectors[:, np.argmax(eigenvalues)]
    return float(np.degrees(np.arctan2(principal[1], principal[0])))


# ── Step 2: 화살촉 쌍 매칭 → 치수선 복원 ───────────────────

def match_arrowhead_pairs(
    arrowheads: List[Dict],
    lsd_lines: Optional[List[Dict]] = None,
    angle_tolerance: float = 15.0,
    min_distance: float = 20.0,
    max_distance: float = 2000.0,
) -> List[Dict]:
    """동일 치수선 위의 화살촉 쌍 찾기

    판정 기준:
    - 연결 방향 vs 각 화살촉 각도 차이 ≤ angle_tolerance
    - 거리: min_distance ~ max_distance
    - LSD 선분 지지 시 score 보너스

    Returns:
        [{start, end, midpoint, direction, length, score}, ...]
    """
    if len(arrowheads) < 2:
        return []

    n = len(arrowheads)
    pts = np.array([[a["x"], a["y"]] for a in arrowheads], dtype=np.float32)
    angles = np.array([a["angle"] for a in arrowheads], dtype=np.float32)
    used = np.zeros(n, dtype=bool)
    dim_lines = []

    for i in range(n):
        if used[i]:
            continue
        best_j, best_score = -1, -1.0

        for j in range(i + 1, n):
            if used[j]:
                continue
            dx, dy = pts[j, 0] - pts[i, 0], pts[j, 1] - pts[i, 1]
            dist = float(np.sqrt(dx * dx + dy * dy))
            if dist < min_distance or dist > max_distance:
                continue
            link_angle = float(np.degrees(np.arctan2(dy, dx)))
            diff_i = _angle_diff(angles[i], link_angle)
            diff_j = _angle_diff(angles[j], link_angle)
            if diff_i > angle_tolerance and diff_j > angle_tolerance:
                continue
            score = 1.0 / (1.0 + (diff_i + diff_j) * 0.1) / (1.0 + dist * 0.001)
            if lsd_lines is not None and len(lsd_lines) > 0:
                mx = (pts[i, 0] + pts[j, 0]) / 2
                my = (pts[i, 1] + pts[j, 1]) / 2
                score += _lsd_support(mx, my, link_angle, dist, lsd_lines) * 0.5
            if score > best_score:
                best_score, best_j = score, j

        if best_j >= 0:
            dx, dy = pts[best_j, 0] - pts[i, 0], pts[best_j, 1] - pts[i, 1]
            dist = float(np.sqrt(dx * dx + dy * dy))
            dim_lines.append({
                "start": {"x": float(pts[i, 0]), "y": float(pts[i, 1])},
                "end": {"x": float(pts[best_j, 0]), "y": float(pts[best_j, 1])},
                "midpoint": {"x": float((pts[i, 0] + pts[best_j, 0]) / 2),
                             "y": float((pts[i, 1] + pts[best_j, 1]) / 2)},
                "direction": float(np.degrees(np.arctan2(dy, dx))),
                "length": dist,
                "score": best_score,
            })
            used[i] = used[best_j] = True

    logger.info(f"치수선 쌍 매칭: {len(dim_lines)}개 (화살촉 {n}개)")
    return dim_lines


def _angle_diff(a: float, b: float) -> float:
    """두 각도의 최소 차이 (0~90, 방향 모호성 고려)"""
    diff = abs(a - b) % 180.0
    return 180.0 - diff if diff > 90.0 else diff


def _lsd_support(
    mx: float, my: float, direction: float, length: float,
    lsd_lines, tol: float = 10.0,
) -> float:
    """LSD 선분이 치수선을 지지하면 1.0, 아니면 0.0"""
    for seg in lsd_lines:
        if isinstance(seg, np.ndarray):
            sx1, sy1, sx2, sy2 = seg[0], seg[1], seg[2], seg[3]
        else:
            sx1, sy1 = seg.get("x1", 0), seg.get("y1", 0)
            sx2, sy2 = seg.get("x2", 0), seg.get("y2", 0)
        smx, smy = (sx1 + sx2) / 2, (sy1 + sy2) / 2
        if np.sqrt((smx - mx) ** 2 + (smy - my) ** 2) > length * 0.6:
            continue
        seg_angle = float(np.degrees(np.arctan2(sy2 - sy1, sx2 - sx1)))
        if _angle_diff(seg_angle, direction) < tol:
            return 1.0
    return 0.0


# ── Step 3: 치수선-텍스트 매칭 ──────────────────────────────

def match_dimensions_to_lines(
    dim_lines: List[Dict],
    ocr_texts: List[Dict],
) -> List[Dict]:
    """각 치수선 중점과 가장 가까운 OCR 텍스트 bbox 매핑

    거리 임계값: max(line_length × 0.5, 30px).

    Returns:
        [{dim_line, text_value, num_val, distance, is_diameter, is_radius, bbox, confidence}, ...]
        num_val: R 접두사면 직경으로 변환된 값
    """
    if not dim_lines or not ocr_texts:
        return []

    # 텍스트 중점 배열 사전 계산
    text_centers = []
    for t in ocr_texts:
        bbox = t.get("bbox", {}) if isinstance(t, dict) else {}
        if isinstance(bbox, dict):
            text_centers.append((
                (bbox.get("x1", 0) + bbox.get("x2", 0)) / 2.0,
                (bbox.get("y1", 0) + bbox.get("y2", 0)) / 2.0,
            ))
        else:
            text_centers.append((
                (getattr(bbox, "x1", 0) + getattr(bbox, "x2", 0)) / 2.0,
                (getattr(bbox, "y1", 0) + getattr(bbox, "y2", 0)) / 2.0,
            ))

    if not text_centers:
        return []

    tc_arr = np.array(text_centers, dtype=np.float64)
    matched = []

    for dl in dim_lines:
        mid = dl.get("midpoint", {})
        mx, my = mid.get("x", 0.0), mid.get("y", 0.0)
        threshold = max(dl.get("length", 1.0) * 0.5, 30.0)

        dists = np.sqrt(((tc_arr - np.array([mx, my])) ** 2).sum(axis=1))
        valid = np.where(dists < threshold)[0]
        if len(valid) == 0:
            continue

        idx = valid[np.argmin(dists[valid])]
        t = ocr_texts[idx]
        val_str = (t.get("value", "") if isinstance(t, dict) else "").strip()

        is_diameter = bool(re.match(r'^[ØøΦ⌀∅]', val_str))
        is_radius = bool(re.match(r'^[Rr]\s*\d', val_str))
        cleaned = re.sub(r'^[ØøΦ⌀∅Rr]\s*', '', re.sub(r'[()]', '', val_str))
        m = re.match(r'(\d+\.?\d*)', cleaned)
        if not m:
            continue
        num_val = float(m.group(1)) * (2.0 if is_radius else 1.0)
        if num_val < 1.0:
            continue

        bbox_raw = t.get("bbox", {}) if isinstance(t, dict) else {}
        bbox_dict = bbox_raw if isinstance(bbox_raw, dict) else {
            "x1": getattr(bbox_raw, "x1", 0), "y1": getattr(bbox_raw, "y1", 0),
            "x2": getattr(bbox_raw, "x2", 0), "y2": getattr(bbox_raw, "y2", 0),
        }
        matched.append({
            "dim_line": dl,
            "text_value": val_str,
            "num_val": num_val,
            "distance": float(dists[idx]),
            "is_diameter": is_diameter,
            "is_radius": is_radius,
            "bbox": bbox_dict,
            "confidence": t.get("confidence", 0.5) if isinstance(t, dict) else 0.5,
        })

    logger.info(f"치수선-텍스트 매칭: {len(matched)}개 ({len(dim_lines)}개 치수선)")
    return matched


# ── Step 4: OD/ID/W 분류 ────────────────────────────────────

def classify_od_id_w_by_arrowhead(
    matched_dims: List[Dict],
    outer_circle: Optional[Tuple] = None,
    inner_circle: Optional[Tuple] = None,
) -> Dict:
    """화살촉 치수선으로 OD/ID/W 분류

    규칙:
    - 치수선 방향이 원 중심 관통(±30°) → 직경 후보
    - 수직/축 방향(80~100°) → W 후보
    - Ø 접두사 → confidence +0.3 보너스
    - 직경 후보 최대 = OD, 2번째 = ID

    Returns:
        {"od": {value, confidence, bbox}, "id": ..., "w": ...} (없으면 None)
    """
    if not matched_dims:
        return {"od": None, "id": None, "w": None}

    has_circle = outer_circle is not None
    cx_o = float(outer_circle[0]) if has_circle else 0.0
    cy_o = float(outer_circle[1]) if has_circle else 0.0
    r_o = float(outer_circle[2]) if has_circle else 0.0

    diameter_cands: List[Dict] = []
    width_cands: List[Dict] = []

    for md in matched_dims:
        dl = md["dim_line"]
        direction = dl.get("direction", 0.0)
        mid = dl.get("midpoint", {})
        mx, my = mid.get("x", 0.0), mid.get("y", 0.0)
        num_val, conf = md["num_val"], md["confidence"]
        is_diameter, is_radius = md["is_diameter"], md["is_radius"]

        norm_dir = direction % 180.0
        if norm_dir > 90.0:
            norm_dir -= 180.0

        # 직경 여부 판정
        is_dia = False
        dia_conf = conf
        if has_circle:
            vec = np.array([cx_o - mx, cy_o - my], dtype=np.float64)
            vlen = np.linalg.norm(vec)
            if vlen > 1e-3:
                ca = float(np.degrees(np.arctan2(vec[1], vec[0])))
                diff = _angle_diff(direction, ca)
                if diff <= 30.0:
                    is_dia = True
                    dia_conf = conf * (1.0 - diff / 60.0)
        else:
            is_dia = abs(norm_dir) <= 45.0

        if is_diameter or is_radius:
            is_dia = True
            dia_conf = min(1.0, dia_conf + 0.3)

        is_width = 80.0 <= abs(norm_dir) <= 100.0

        entry = {
            "value": md["text_value"],
            "num_val": num_val,
            "confidence": dia_conf if is_dia else conf,
            "bbox": md["bbox"],
        }
        if is_dia:
            diameter_cands.append(entry)
        elif is_width:
            width_cands.append(entry)
        else:
            # 방향 불명 → 값 크기로 보조 분류
            (diameter_cands if (has_circle and num_val > r_o * 0.5) else width_cands).append(entry)

    diameter_cands.sort(key=lambda c: c["num_val"], reverse=True)
    od = diameter_cands[0] if diameter_cands else None
    id_val = None
    for c in diameter_cands[1:]:
        if od and c["num_val"] < od["num_val"] and c["num_val"] >= od["num_val"] * 0.10:
            id_val = c
            break

    used = {e["value"] for e in [od, id_val] if e}
    w = next((c for c in sorted(width_cands, key=lambda c: c["confidence"], reverse=True)
               if c["value"] not in used), None)
    if w is None:
        w = next((c for c in diameter_cands if c is not od and c is not id_val
                  and c["value"] not in used), None)

    logger.info(
        f"arrowhead 분류: OD={od['value'] if od else 'N/A'}, "
        f"ID={id_val['value'] if id_val else 'N/A'}, "
        f"W={w['value'] if w else 'N/A'}"
    )
    return {"od": _fmt(od), "id": _fmt(id_val), "w": _fmt(w)}


def _fmt(e: Optional[Dict]) -> Optional[Dict]:
    """결과 표준 형식 변환"""
    if e is None:
        return None
    return {"value": e["value"], "confidence": round(float(e["confidence"]), 3), "bbox": e.get("bbox", {})}


# ── 통합 파이프라인 ──────────────────────────────────────────

def run_arrowhead_pipeline(
    img_gray: np.ndarray,
    ocr_texts: List[Dict],
    lsd_lines: Optional[List[Dict]] = None,
    outer_circle: Optional[Tuple] = None,
    inner_circle: Optional[Tuple] = None,
) -> Dict:
    """Step 1~4 통합 실행: 화살촉 검출 → 쌍 매칭 → 텍스트 매핑 → OD/ID/W 분류

    Args:
        img_gray: 그레이스케일 도면 이미지
        ocr_texts: OCR 결과 목록
        lsd_lines: LSD 선분 목록 (교차 검증용, 없으면 None)
        outer_circle: (cx, cy, r) 외경 원
        inner_circle: (cx, cy, r) 내경 원 (현재 미사용, 확장 예약)

    Returns:
        {od, id, w, arrowheads, dim_lines, matched_dims, debug}
    """
    arrowheads = detect_arrowheads(img_gray)
    dim_lines = match_arrowhead_pairs(arrowheads, lsd_lines)
    matched_dims = match_dimensions_to_lines(dim_lines, ocr_texts)
    result = classify_od_id_w_by_arrowhead(matched_dims, outer_circle, inner_circle)

    result["arrowheads"] = arrowheads
    result["dim_lines"] = dim_lines
    result["matched_dims"] = [
        {
            "text_value": m["text_value"],
            "num_val": m["num_val"],
            "distance": round(m["distance"], 1),
            "is_diameter": m["is_diameter"],
            "is_radius": m["is_radius"],
        }
        for m in matched_dims
    ]
    result["debug"] = {
        "arrowhead_count": len(arrowheads),
        "dim_line_count": len(dim_lines),
        "matched_dim_count": len(matched_dims),
        "has_outer_circle": outer_circle is not None,
        "has_inner_circle": inner_circle is not None,
    }
    return result
