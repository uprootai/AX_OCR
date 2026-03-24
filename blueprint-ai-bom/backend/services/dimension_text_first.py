"""Text-First 치수 추출 — OCR 먼저, 치수선 역추적

파이프라인: OCR 결과 입력 → Ø/R 텍스트 파싱 → LSD 치수선 탐색 → 방향 분류 → OD/ID/W 결정

원 검출에 의존하지 않는다. Ø 접두사 텍스트를 1차 단서로,
치수선 방향을 분류 근거로 활용한다.
"""
import re
import logging
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ── 정규식 상수 ──────────────────────────────────────────────────────────────
_RE_DIAMETER_PREFIX = re.compile(r'^[ØøΦ⌀∅]')
_RE_RADIUS_PREFIX = re.compile(r'^[Rr](?!\s*[A-Za-z])')
_RE_NUMBER = re.compile(r'(\d+\.?\d*)')
_RE_THREAD = re.compile(r'^M\d', re.IGNORECASE)
_RE_NON_DIM = re.compile(r'[°]|deg|UNC|UNF|TPI', re.IGNORECASE)
_RE_STRIP_PREFIX = re.compile(r'^[ØøΦ⌀∅Rr]\s*')


# ── Step 1: OCR 결과 파싱 ────────────────────────────────────────────────────

def parse_dimension_texts(ocr_results: list) -> List[Dict]:
    """OCR 결과에서 치수 텍스트 파싱. Ø/R 접두사, 숫자값, 공차 식별.

    나사산(M16), 각도(°), 참조치수((580))는 제외한다.
    Returns: [{text, num_val, is_diameter, is_radius, bbox, confidence, tolerance}]
    """
    parsed: List[Dict] = []

    for item in ocr_results:
        if isinstance(item, dict):
            raw_text = item.get("value", "").strip()
            bbox = item.get("bbox")
            confidence = item.get("confidence", 0.5)
        else:
            raw_text = (item.value.strip() if hasattr(item, "value") else str(item))
            bbox = item.bbox if hasattr(item, "bbox") else None
            confidence = item.confidence if hasattr(item, "confidence") else 0.5

        if not raw_text or bbox is None:
            continue

        # 제외: 나사산, 각도/비치수, 참조치수(괄호 전체)
        if _RE_THREAD.match(raw_text):
            logger.debug(f"나사산 제외: {raw_text!r}")
            continue
        if _RE_NON_DIM.search(raw_text):
            logger.debug(f"비치수 제외: {raw_text!r}")
            continue
        if raw_text.startswith("(") and raw_text.endswith(")"):
            logger.debug(f"참조치수 제외: {raw_text!r}")
            continue

        is_diameter = bool(_RE_DIAMETER_PREFIX.match(raw_text))
        is_radius = bool(_RE_RADIUS_PREFIX.match(raw_text)) and not is_diameter

        cleaned = _RE_STRIP_PREFIX.sub("", raw_text)
        cleaned = re.sub(r"[()]", "", cleaned)
        m = _RE_NUMBER.match(cleaned)
        if not m:
            continue
        num_val = float(m.group(1))
        if num_val < 5:
            continue

        # 공차 파싱 (+0.03/-0.02 형태)
        tolerance = None
        tol_m = re.search(r'([+\-]\d+\.?\d*)\s*/?\s*([+\-]\d+\.?\d*)', cleaned)
        if tol_m:
            tolerance = {"upper": tol_m.group(1), "lower": tol_m.group(2)}

        # bbox 정규화
        if isinstance(bbox, dict):
            bbox_dict = bbox
        elif isinstance(bbox, (list, tuple)) and len(bbox) >= 2:
            # [[x1,y1],[x2,y2],...] 형태 → x1/y1/x2/y2 변환
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            bbox_dict = {"x1": min(xs), "y1": min(ys), "x2": max(xs), "y2": max(ys)}
        elif hasattr(bbox, "x1"):
            bbox_dict = {"x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2}
        else:
            continue

        parsed.append({
            "text": raw_text,
            "num_val": num_val,
            "is_diameter": is_diameter,
            "is_radius": is_radius,
            "bbox": bbox_dict,
            "confidence": confidence,
            "tolerance": tolerance,
        })

    logger.info(
        f"치수 파싱 완료: 입력 {len(ocr_results)}개 → 유효 {len(parsed)}개 "
        f"(Ø={sum(1 for p in parsed if p['is_diameter'])}, "
        f"R={sum(1 for p in parsed if p['is_radius'])})"
    )
    return parsed


# ── Step 2: 텍스트 bbox 주변 치수선 탐색 ────────────────────────────────────

def find_nearby_dimension_lines(
    text_bbox: Dict,
    lsd_lines: np.ndarray,
    expand_px: int = 50,
) -> Optional[Dict]:
    """텍스트 bbox를 expand_px 확장 후 교차하는 LSD 선분 중 가장 긴 것을 반환한다.

    Returns: {start, end, direction_angle, length} 또는 None
    """
    if lsd_lines is None or len(lsd_lines) == 0:
        return None

    ex1 = text_bbox["x1"] - expand_px
    ey1 = text_bbox["y1"] - expand_px
    ex2 = text_bbox["x2"] + expand_px
    ey2 = text_bbox["y2"] + expand_px

    best: Optional[Dict] = None
    best_len = 0.0

    for seg in lsd_lines:
        coords = seg[0] if seg.ndim == 2 else seg
        x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if length < 20:
            continue

        if not _segment_intersects_bbox(x1, y1, x2, y2, ex1, ey1, ex2, ey2):
            continue

        if length > best_len:
            best_len = length
            best = {
                "start": (x1, y1),
                "end": (x2, y2),
                "direction_angle": float(np.degrees(np.arctan2(y2 - y1, x2 - x1))),
                "length": length,
            }

    return best


def _segment_intersects_bbox(
    x1: float, y1: float, x2: float, y2: float,
    bx1: float, by1: float, bx2: float, by2: float,
) -> bool:
    """선분이 축정렬 사각형과 교차하는지 확인한다."""
    def _inside(px, py):
        return bx1 <= px <= bx2 and by1 <= py <= by2

    if _inside(x1, y1) or _inside(x2, y2):
        return True

    for ex1_, ey1_, ex2_, ey2_ in [
        (bx1, by1, bx2, by1), (bx1, by2, bx2, by2),
        (bx1, by1, bx1, by2), (bx2, by1, bx2, by2),
    ]:
        if _segments_cross(x1, y1, x2, y2, ex1_, ey1_, ex2_, ey2_):
            return True
    return False


def _segments_cross(
    ax1: float, ay1: float, ax2: float, ay2: float,
    bx1: float, by1: float, bx2: float, by2: float,
) -> bool:
    """두 선분 교차 여부 — 외적(cross product) 기반."""
    def _cross(ox, oy, ax, ay, bx, by):
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    d1 = _cross(bx1, by1, bx2, by2, ax1, ay1)
    d2 = _cross(bx1, by1, bx2, by2, ax2, ay2)
    d3 = _cross(ax1, ay1, ax2, ay2, bx1, by1)
    d4 = _cross(ax1, ay1, ax2, ay2, bx2, by2)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    # 공선 처리
    def _on_seg(px, py, qx, qy, rx, ry):
        return min(px, rx) <= qx <= max(px, rx) and min(py, ry) <= qy <= max(py, ry)

    if d1 == 0 and _on_seg(bx1, by1, ax1, ay1, bx2, by2):
        return True
    if d2 == 0 and _on_seg(bx1, by1, ax2, ay2, bx2, by2):
        return True
    if d3 == 0 and _on_seg(ax1, ay1, bx1, by1, ax2, ay2):
        return True
    if d4 == 0 and _on_seg(ax1, ay1, bx2, by2, ax2, ay2):
        return True
    return False


# ── Step 3: 치수선 방향 기반 OD/ID/W 분류 ───────────────────────────────────

def classify_by_line_direction(
    matched_pairs: List[Dict],
    outer_circle: Optional[np.ndarray] = None,
) -> Dict:
    """텍스트-치수선 매칭 결과를 OD/ID/W로 분류한다.

    수평(±15°) + Ø → 직경 후보, 수직(75~105°) → W 후보.
    직경 후보 최대=OD, 차대=ID(5% 이상 차이 필요).
    outer_circle 제공 시 원 중심 관통 선분 confidence +0.3.

    Returns: {od, id, w} 각 dict|None
    """
    diameter_candidates: List[Dict] = []
    width_candidates: List[Dict] = []

    for pair in matched_pairs:
        pt = pair["parsed_text"]
        dl = pair.get("dim_line")

        is_dia = pt["is_diameter"]
        is_rad = pt["is_radius"]
        diameter_val = pt["num_val"] * 2 if is_rad else pt["num_val"]
        conf = pt["confidence"]

        entry = {
            "text": pt["text"],
            "num_val": diameter_val,
            "confidence": conf,
            "bbox": pt["bbox"],
            "source": "text_first",
            "has_diameter_prefix": is_dia or is_rad,
            "dim_line": dl,
        }

        if dl is None:
            # 치수선 없음 — Ø/R 접두사면 낮은 신뢰도로 직경 후보 유지
            if is_dia or is_rad:
                entry["confidence"] = conf * 0.7
                diameter_candidates.append(entry)
            continue

        # outer_circle 보조: 원 중심 관통 시 confidence 보강
        if outer_circle is not None:
            cx, cy = float(outer_circle[0]), float(outer_circle[1])
            if _line_passes_near_point(dl["start"], dl["end"], cx, cy, tolerance=50):
                entry["confidence"] = min(1.0, conf + 0.3)
                logger.debug(f"원 중심 관통 보강: {pt['text']!r} conf→{entry['confidence']:.2f}")

        abs_angle = abs(dl["direction_angle"]) % 180
        is_horizontal = abs_angle <= 15 or abs_angle >= 165
        is_vertical = 75 <= abs_angle <= 105

        # Ø/R 접두사 → 방향 무관하게 직경 후보 (베어링 도면에서 수직 기입 빈번)
        if is_dia or is_rad:
            if not is_horizontal:
                entry["confidence"] = conf * 0.8
            diameter_candidates.append(entry)
        elif is_horizontal and diameter_val >= 50:
            entry["confidence"] = conf * 0.8
            diameter_candidates.append(entry)
        elif is_vertical:
            width_candidates.append(entry)

    logger.info(
        f"분류: 직경후보 {len(diameter_candidates)}개, 폭후보 {len(width_candidates)}개"
    )

    # OD/ID 선택: num_val 내림차순 + W 물리관계 검증
    diameter_candidates.sort(key=lambda x: (x["num_val"], x["confidence"]), reverse=True)
    od_entry = diameter_candidates[0] if diameter_candidates else None
    id_entry = None

    # W 먼저 선택 (ID 검증에 활용)
    width_candidates.sort(key=lambda x: x["confidence"], reverse=True)
    w_entry = width_candidates[0] if width_candidates else None

    if len(diameter_candidates) >= 2 and od_entry:
        od_val = od_entry["num_val"]
        id_candidates = [c for c in diameter_candidates[1:]
                         if c["num_val"] < od_val * 0.95 and c["num_val"] >= od_val * 0.10]

        if id_candidates and w_entry:
            # W 후보가 있을 때: Ø 접두사 우선, 동률 시 값 크기순
            id_candidates.sort(
                key=lambda x: (x.get("has_diameter_prefix", False), x["num_val"]),
                reverse=True,
            )
            id_entry = id_candidates[0]
        elif id_candidates and not w_entry:
            # W 후보 없음 → 직경 후보 중 가장 작은 값을 W로 전환
            all_non_od = sorted(
                [c for c in diameter_candidates if c is not od_entry],
                key=lambda x: x["num_val"],
            )
            # 가장 작은 비-Ø 값을 W로
            w_cands = [c for c in all_non_od if not c.get("has_diameter_prefix", False)]
            if w_cands:
                w_entry = w_cands[0]
                logger.info(f"W 전환: {w_entry['text']} (최소 비-Ø 값)")
            # 나머지에서 ID 선택: Ø 우선 → 값 크기순
            remaining = [c for c in id_candidates if c is not w_entry]
            if remaining:
                remaining.sort(
                    key=lambda x: (x.get("has_diameter_prefix", False), x["num_val"]),
                    reverse=True,
                )
                id_entry = remaining[0]
            elif id_candidates:
                id_entry = id_candidates[0]

    if w_entry and od_entry and w_entry["num_val"] >= od_entry["num_val"]:
        logger.warning(f"W({w_entry['num_val']}) >= OD({od_entry['num_val']}) — W 제거")
        w_entry = None

    return {
        "od": _to_result(od_entry),
        "id": _to_result(id_entry),
        "w": _to_result(w_entry),
    }


def _line_passes_near_point(
    start: Tuple[float, float],
    end: Tuple[float, float],
    px: float, py: float,
    tolerance: float = 50,
) -> bool:
    """선분이 점 (px, py)에서 tolerance px 이내를 통과하는지 확인한다."""
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-9:
        return False
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_len_sq))
    dist = np.sqrt((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2)
    return dist <= tolerance


def _to_result(entry: Optional[Dict]) -> Optional[Dict]:
    """분류 항목 → 표준 결과 형식 변환."""
    if entry is None:
        return None
    return {
        "value": entry["text"],
        "confidence": round(entry["confidence"], 3),
        "bbox": entry["bbox"],
        "source": entry.get("source", "text_first"),
        "has_diameter_prefix": entry.get("has_diameter_prefix", False),
    }


# ── Step 4: 통합 파이프라인 ──────────────────────────────────────────────────

def extract_text_first(
    dims: List[Dict],
    img_gray: np.ndarray,
    outer_circle: Optional[np.ndarray] = None,
) -> Dict:
    """Text-First 통합 파이프라인 — 원 검출 없이 독립 동작.

    OCR 결과(dims)를 입력받아 파싱 → LSD → 매칭 → 분류 순서로 처리한다.
    OCR을 직접 호출하지 않는다.

    Returns: {od, id, w, debug}  (debug: parsed_count, lsd_line_count, matched_count, ...)
    """
    parsed_texts = parse_dimension_texts(dims)
    if not parsed_texts:
        logger.warning("Text-First: 유효한 치수 텍스트 없음")
        return {
            "od": None, "id": None, "w": None,
            "debug": {
                "parsed_count": 0, "lsd_line_count": 0,
                "matched_count": 0, "unmatched_count": 0,
                "diameter_candidates": 0, "width_candidates": 0,
            },
        }

    # LSD 치수선 검출
    lsd_lines = _run_lsd(img_gray)
    n_lsd = len(lsd_lines) if lsd_lines is not None else 0
    logger.info(f"LSD 선분 검출: {n_lsd}개")

    # 텍스트-치수선 매칭
    matched_pairs: List[Dict] = []
    matched_count = 0
    unmatched_count = 0

    for pt in parsed_texts:
        dl = find_nearby_dimension_lines(pt["bbox"], lsd_lines, expand_px=50)
        matched_pairs.append({"parsed_text": pt, "dim_line": dl})
        if dl is not None:
            matched_count += 1
            logger.debug(
                f"매칭: {pt['text']!r} ← angle={dl['direction_angle']:.1f}° len={dl['length']:.0f}px"
            )
        else:
            unmatched_count += 1
            logger.debug(f"미매칭: {pt['text']!r}")

    logger.info(f"텍스트-치수선 매칭: {matched_count}개 성공, {unmatched_count}개 실패")

    classification = classify_by_line_direction(matched_pairs, outer_circle)

    n_diameter = sum(
        1 for p in matched_pairs
        if p["dim_line"] is not None and _is_horizontal_angle(p["dim_line"]["direction_angle"])
    )
    n_width = sum(
        1 for p in matched_pairs
        if p["dim_line"] is not None and _is_vertical_angle(p["dim_line"]["direction_angle"])
    )

    result = {**classification, "debug": {
        "parsed_count": len(parsed_texts),
        "lsd_line_count": n_lsd,
        "matched_count": matched_count,
        "unmatched_count": unmatched_count,
        "diameter_candidates": n_diameter,
        "width_candidates": n_width,
    }}

    logger.info(
        f"Text-First 결과: OD={result['od']['value'] if result['od'] else 'N/A'}, "
        f"ID={result['id']['value'] if result['id'] else 'N/A'}, "
        f"W={result['w']['value'] if result['w'] else 'N/A'}"
    )
    return result


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _run_lsd(img_gray: np.ndarray) -> Optional[np.ndarray]:
    """LSD 선분 검출. 1500px 초과 시 리사이즈 후 좌표 역변환."""
    if img_gray is None or img_gray.size == 0:
        return None

    orig_h, orig_w = img_gray.shape[:2]
    max_dim = 1500
    scale = 1.0
    work_img = img_gray

    if max(orig_h, orig_w) > max_dim:
        scale = max_dim / max(orig_h, orig_w)
        work_img = cv2.resize(img_gray, (int(orig_w * scale), int(orig_h * scale)))

    try:
        lsd = cv2.createLineSegmentDetector(0)
        lines, _, _, _ = lsd.detect(work_img)
    except Exception as e:
        logger.error(f"LSD 검출 실패: {e}")
        return None

    if lines is None:
        return None

    if scale != 1.0:
        lines = lines / scale

    return lines


def _is_horizontal_angle(angle_deg: float) -> bool:
    """수평 각도 여부 (±15° 또는 ±165°)."""
    a = abs(angle_deg) % 180
    return a <= 15 or a >= 165


def _is_vertical_angle(angle_deg: float) -> bool:
    """수직 각도 여부 (75°~105°)."""
    return 75 <= abs(angle_deg) % 180 <= 105
