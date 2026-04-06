"""ROI and dimension-line helpers for geometry-guided extraction."""

import logging
from typing import Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _detect_dimension_lines(
    img_gray: np.ndarray,
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> List[Dict]:
    """원 주변의 치수선(직선) 검출 — LSD 기반."""
    lsd = cv2.createLineSegmentDetector(0)
    lines, widths, prec, nfa = lsd.detect(img_gray)

    if lines is None:
        return []

    cx, cy, r_outer = int(outer[0]), int(outer[1]), int(outer[2])
    dim_lines = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if length < 30:
            continue

        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dist_to_center = np.sqrt((mx - cx) ** 2 + (my - cy) ** 2)

        if dist_to_center < r_outer * 0.5 or dist_to_center > r_outer * 3.5:
            continue

        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if angle < 15 or angle > 165:
            direction = "horizontal"
        elif 75 < angle < 105:
            direction = "vertical"
        else:
            continue

        for px, py in [(x1, y1), (x2, y2)]:
            dist_from_edge = abs(np.sqrt((px - cx) ** 2 + (py - cy) ** 2) - r_outer)
            if dist_from_edge < r_outer * 0.3:
                dim_lines.append(
                    {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2),
                        "direction": direction,
                        "length": float(length),
                        "dist_to_center": float(dist_to_center),
                    }
                )
                break

    dim_lines.sort(key=lambda line: line["length"], reverse=True)
    dim_lines = dim_lines[:8]
    logger.info(f"치수선 후보 {len(dim_lines)}개 (원 cx={cx}, cy={cy}, r={r_outer})")
    return dim_lines


def _extract_rois_from_dim_lines(
    dim_lines: List[Dict],
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> List[Dict]:
    """치수선 끝점 근처에 텍스트 ROI 생성."""
    cx, cy = int(outer[0]), int(outer[1])
    rois = []
    pad = 60

    for line in dim_lines:
        d1 = np.sqrt((line["x1"] - cx) ** 2 + (line["y1"] - cy) ** 2)
        d2 = np.sqrt((line["x2"] - cx) ** 2 + (line["y2"] - cy) ** 2)
        if d1 > d2:
            tx, ty = line["x1"], line["y1"]
        else:
            tx, ty = line["x2"], line["y2"]

        roi = {
            "x1": max(0, int(tx) - pad),
            "y1": max(0, int(ty) - pad),
            "x2": min(orig_w, int(tx) + pad),
            "y2": min(orig_h, int(ty) + pad),
            "direction": line["direction"],
            "source": "dim_line",
        }
        if not any(_rois_overlap(roi, existing) for existing in rois):
            rois.append(roi)

    return rois


def _extract_rois_from_circle_edges(
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> List[Dict]:
    """원 동서남북 가장자리 바깥에 ROI 생성 (치수선 미검출 시 대비)."""
    cx, cy, r = int(outer[0]), int(outer[1]), int(outer[2])
    margin = int(r * 0.3)
    text_w, text_h = 120, 50

    edge_rois = [
        {
            "x1": cx - text_w,
            "y1": max(0, cy - r - margin - text_h),
            "x2": cx + text_w,
            "y2": cy - r - margin + text_h,
            "direction": "vertical",
            "source": "edge_north",
        },
        {
            "x1": cx - text_w,
            "y1": cy + r + margin - text_h,
            "x2": cx + text_w,
            "y2": min(orig_h, cy + r + margin + text_h),
            "direction": "vertical",
            "source": "edge_south",
        },
        {
            "x1": cx + r + margin - text_w,
            "y1": cy - text_h,
            "x2": min(orig_w, cx + r + margin + text_w),
            "y2": cy + text_h,
            "direction": "horizontal",
            "source": "edge_east",
        },
        {
            "x1": max(0, cx - r - margin - text_w),
            "y1": cy - text_h,
            "x2": cx - r - margin + text_w,
            "y2": cy + text_h,
            "direction": "horizontal",
            "source": "edge_west",
        },
    ]

    valid = []
    for roi in edge_rois:
        roi["x1"] = max(0, roi["x1"])
        roi["y1"] = max(0, roi["y1"])
        roi["x2"] = min(orig_w, roi["x2"])
        roi["y2"] = min(orig_h, roi["y2"])
        if roi["x2"] - roi["x1"] > 20 and roi["y2"] - roi["y1"] > 20:
            valid.append(roi)

    return valid


def _rois_overlap(a: Dict, b: Dict, threshold: float = 0.5) -> bool:
    """두 ROI가 겹치는지."""
    x_overlap = max(0, min(a["x2"], b["x2"]) - max(a["x1"], b["x1"]))
    y_overlap = max(0, min(a["y2"], b["y2"]) - max(a["y1"], b["y1"]))
    overlap_area = x_overlap * y_overlap
    a_area = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    return overlap_area > a_area * threshold if a_area > 0 else False


def _ocr_rois(
    image_path: str,
    img_gray: np.ndarray,
    rois: List[Dict],
    ocr_engine: str,
    confidence_threshold: float,
) -> List[Dict]:
    """각 ROI 영역을 크롭하여 OCR 실행."""
    import os
    import tempfile

    from services.dimension_service import DimensionService

    dim_service = DimensionService()
    results = []
    fail_count = 0

    for roi in rois[:12]:
        if fail_count >= 3:
            logger.warning("ROI OCR 연속 실패 — 나머지 스킵")
            break
        crop = img_gray[roi["y1"] : roi["y2"], roi["x1"] : roi["x2"]]
        if crop.size == 0:
            continue

        scale_factor = max(1, 100 // max(crop.shape[:2]))
        if scale_factor > 1:
            crop = cv2.resize(
                crop,
                None,
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_CUBIC,
            )

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                cv2.imwrite(handle.name, crop)
                tmp_path = handle.name

            ocr_result = dim_service.extract_dimensions(
                tmp_path,
                confidence_threshold,
                [ocr_engine],
            )
            dims = ocr_result.get("dimensions", [])

            fail_count = 0
            for dim in dims:
                if isinstance(dim, dict):
                    bbox = dim.get("bbox", {})
                    if isinstance(bbox, dict):
                        dim["bbox"] = {
                            "x1": roi["x1"] + int(bbox.get("x1", 0) / max(scale_factor, 1)),
                            "y1": roi["y1"] + int(bbox.get("y1", 0) / max(scale_factor, 1)),
                            "x2": roi["x1"] + int(bbox.get("x2", 0) / max(scale_factor, 1)),
                            "y2": roi["y1"] + int(bbox.get("y2", 0) / max(scale_factor, 1)),
                        }
                    dim["roi_direction"] = roi.get("direction", "unknown")
                    dim["roi_source"] = roi.get("source", "unknown")
                    results.append(dim)

        except Exception as exc:
            fail_count += 1
            logger.warning(f"ROI OCR 실패 ({roi.get('source', '?')}): {exc}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    logger.info(f"ROI OCR 결과: {len(results)}개 치수 ({len(rois)}개 ROI)")
    return results


def _assign_roles(
    ocr_results: List[Dict],
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> Dict:
    """치수선 방향 + 원과의 관계로 OD/ID/W 역할 결정."""
    import re

    cx, cy, r_outer = int(outer[0]), int(outer[1]), int(outer[2])
    r_inner = int(inner[2]) if inner is not None else r_outer // 2

    od_candidates = []
    id_candidates = []
    w_candidates = []

    for result in ocr_results:
        value_str = result.get("value", "")
        nums = re.findall(
            r"[\d.]+",
            value_str.replace("Ø", "").replace("ø", "").replace("R", ""),
        )
        if not nums:
            continue
        try:
            num_val = float(nums[0])
        except ValueError:
            continue

        if num_val < 5:
            continue

        bbox = result.get("bbox", {})
        dim_cx = (bbox.get("x1", 0) + bbox.get("x2", 0)) / 2
        dim_cy = (bbox.get("y1", 0) + bbox.get("y2", 0)) / 2
        direction = result.get("roi_direction", "unknown")
        confidence = result.get("confidence", 0.5)

        is_radius = (
            value_str.strip().upper().startswith("R")
            and not value_str.strip().upper().startswith("RA")
        )
        diameter_val = num_val * 2 if is_radius else num_val

        entry = {
            "value": value_str,
            "numeric": num_val,
            "diameter": diameter_val,
            "confidence": confidence,
            "bbox": bbox,
            "direction": direction,
        }

        if direction == "vertical":
            dist = np.sqrt((dim_cx - cx) ** 2 + (dim_cy - cy) ** 2)
            if dist > r_outer * 0.8 or diameter_val > r_inner * 2:
                od_candidates.append(entry)
            else:
                id_candidates.append(entry)
        elif direction == "horizontal":
            w_candidates.append(entry)
        else:
            if diameter_val > r_inner * 2:
                od_candidates.append(entry)
            elif diameter_val > num_val * 0.3:
                id_candidates.append(entry)
            else:
                w_candidates.append(entry)

    def _best(candidates):
        if not candidates:
            return None
        return max(candidates, key=lambda candidate: (candidate["diameter"], candidate["confidence"]))

    od = _best(od_candidates)
    id_val = _best(id_candidates)
    w = _best(w_candidates)

    return {
        "od": _format_result(od, "outer_diameter") if od else None,
        "id": _format_result(id_val, "inner_diameter") if id_val else None,
        "w": _format_result(w, "length") if w else None,
    }


def _format_result(entry: Dict, role: str) -> Dict:
    return {
        "value": entry["value"],
        "numeric": entry["numeric"],
        "diameter": entry["diameter"],
        "confidence": entry["confidence"],
        "bbox": entry["bbox"],
        "role": role,
        "direction": entry["direction"],
    }
