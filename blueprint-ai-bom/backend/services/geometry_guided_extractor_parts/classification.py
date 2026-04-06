"""Dimension candidate filtering and classification helpers."""

import logging
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


def filter_ocr_noise(dims: list, r_outer: float = None) -> list:
    """공통 OCR 노이즈 필터 — 날짜, 참조치수, 나사산, 비현실적 값 제거."""
    import re

    filtered = []
    for dim in dims:
        val = (
            dim.get("value", "").strip()
            if isinstance(dim, dict)
            else (dim.value.strip() if hasattr(dim, "value") else "")
        )

        if re.match(r"^\d{4}[-./]\d{1,2}[-./]\d{1,2}", val):
            continue
        if re.match(r"^M\d", val, re.IGNORECASE):
            continue
        if re.search(r"°|deg|UNC|UNF|TPI", val, re.IGNORECASE):
            continue
        if val.startswith("(") and val.endswith(")"):
            continue

        if r_outer:
            has_dia_prefix = bool(re.match(r"^[ØøΦ⌀∅]", val))
            cleaned = re.sub(r"^[ØøΦ⌀∅Rr]\s*", "", val)
            cleaned = re.sub(r"[()]", "", cleaned)
            match = re.match(r"(\d+\.?\d*)", cleaned)
            if match:
                num = float(match.group(1))
                threshold = r_outer * 0.85 if has_dia_prefix else r_outer * 1.0
                if num > threshold:
                    continue

        filtered.append(dim)

    merged = []
    for dim in sorted(
        filtered,
        key=lambda entry: (
            entry.get("confidence", 0.5)
            if isinstance(entry, dict)
            else (entry.confidence if hasattr(entry, "confidence") else 0.5)
        ),
        reverse=True,
    ):
        val = (
            dim.get("value", "").strip()
            if isinstance(dim, dict)
            else (dim.value.strip() if hasattr(dim, "value") else "")
        )
        cleaned = re.sub(r"^[ØøΦ⌀∅Rr]\s*", "", val)
        cleaned = re.sub(r"[()]", "", cleaned)
        match = re.match(r"(\d+\.?\d*)", cleaned)
        if not match:
            merged.append(dim)
            continue
        num = float(match.group(1))
        is_dup = False
        for merged_dim in merged:
            merged_val = (
                merged_dim.get("value", "").strip()
                if isinstance(merged_dim, dict)
                else (
                    merged_dim.value.strip() if hasattr(merged_dim, "value") else ""
                )
            )
            merged_cleaned = re.sub(r"^[ØøΦ⌀∅Rr]\s*", "", merged_val)
            merged_cleaned = re.sub(r"[()]", "", merged_cleaned)
            merged_match = re.match(r"(\d+\.?\d*)", merged_cleaned)
            if merged_match and abs(num - float(merged_match.group(1))) / max(
                float(merged_match.group(1)),
                1,
            ) < 0.05:
                is_dup = True
                break
        if not is_dup:
            merged.append(dim)
    return merged


def _classify_by_circle_proximity(
    dims: list,
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    orig_w: int,
    orig_h: int,
) -> Dict:
    """OCR 치수를 값 크기 기반으로 OD/ID/W 분류."""
    import re

    cx, cy, r_outer = int(outer[0]), int(outer[1]), int(outer[2])
    r_inner = int(inner[2]) if inner is not None else int(r_outer * 0.6)

    candidates = []
    for dim in dims:
        if isinstance(dim, dict):
            val_text = dim.get("value", "").strip()
            bbox = dim.get("bbox")
            confidence = dim.get("confidence", 0.5)
        else:
            val_text = dim.value.strip() if hasattr(dim, "value") else str(dim)
            bbox = dim.bbox if hasattr(dim, "bbox") else None
            confidence = dim.confidence if hasattr(dim, "confidence") else 0.5

        if re.match(r"^M\d", val_text, re.IGNORECASE):
            continue
        if re.search(r"°|deg|UNC|UNF|TPI", val_text, re.IGNORECASE):
            continue
        if re.search(r"NM|N[·.]?m|kgf|kN|lbf", val_text, re.IGNORECASE):
            continue
        if val_text.startswith("(") and val_text.endswith(")"):
            logger.info(f"  참조치수 제외: {val_text}")
            continue

        cleaned = re.sub(r"^[ØøΦ⌀∅Rr]\s*", "", val_text)
        cleaned = re.sub(r"[()]", "", cleaned)
        match = re.match(r"(\d+\.?\d*)", cleaned)
        if not match:
            continue
        num_val = float(match.group(1))
        if num_val < 10:
            continue

        has_diameter_prefix = bool(re.match(r"^[ØøΦ⌀∅]", val_text))
        scale_multiplier = 2.0 if has_diameter_prefix else 1.2
        max_reasonable = r_outer * scale_multiplier
        if num_val > max_reasonable:
            logger.info(
                f"  스케일 필터: {val_text}={num_val} > {max_reasonable} "
                f"(x{scale_multiplier}) 제외"
            )
            continue

        is_radius = bool(re.match(r"^[Rr]\s*\d", val_text))
        display_val = num_val * 2 if is_radius else num_val

        if not bbox:
            continue
        if isinstance(bbox, dict):
            bbox_dict = bbox
        else:
            bbox_dict = {
                "x1": bbox.x1,
                "y1": bbox.y1,
                "x2": bbox.x2,
                "y2": bbox.y2,
            }

        candidates.append(
            {
                "value": val_text,
                "num": display_val,
                "confidence": confidence,
                "bbox": bbox_dict,
            }
        )

    logger.info(
        f"치수 후보 {len(candidates)}개: {[(c['value'], c['num']) for c in candidates]}"
    )

    if not candidates:
        return {
            "od": None,
            "id": None,
            "w": None,
            "rois": [],
            "debug": {"candidates": 0, "total_dims": len(dims)},
        }

    unique = []
    for candidate in sorted(candidates, key=lambda entry: entry["confidence"], reverse=True):
        is_dup = False
        for uniq in unique:
            if abs(candidate["num"] - uniq["num"]) / max(uniq["num"], 1) < 0.02:
                is_dup = True
                break
        if not is_dup:
            unique.append(candidate)
    unique.sort(key=lambda candidate: candidate["num"], reverse=True)
    logger.info(
        f"고유 후보 {len(unique)}개 (내림차순): "
        f"{[(c['value'], c['num']) for c in unique]}"
    )

    od, id_val, w = None, None, None

    dia_outer_px = 2 * r_outer
    dia_inner_px = 2 * r_inner
    has_real_inner = inner is not None

    best_combo = None
    best_score = -1
    max_val = unique[0]["num"] if unique else 1

    if len(unique) >= 2:
        od_cutoff = min(2, len(unique))
        for i, od_c in enumerate(unique[:od_cutoff]):
            scale_od = dia_outer_px / od_c["num"] if od_c["num"] > 0 else 0
            for j, id_c in enumerate(unique):
                if i == j:
                    continue
                if id_c["num"] >= od_c["num"]:
                    continue
                id_min = max(30, od_c["num"] * 0.10)
                if id_c["num"] < id_min:
                    logger.info(
                        f"  ID 후보 제외 ({id_c['num']:.0f} < {id_min:.0f}): "
                        f"{id_c['value']}"
                    )
                    continue

                if has_real_inner:
                    scale_id = dia_inner_px / id_c["num"] if id_c["num"] > 0 else 0
                else:
                    expected_inner_px = id_c["num"] * scale_od
                    inner_ratio = expected_inner_px / dia_outer_px if dia_outer_px > 0 else 0
                    if 0.3 < inner_ratio < 0.9:
                        scale_id = scale_od
                        scale_id *= 1.0 + abs(inner_ratio - 0.6) * 0.1
                    else:
                        scale_id = 0

                if scale_od > 0 and scale_id > 0:
                    consistency = abs(scale_od - scale_id) / max(scale_od, scale_id)
                else:
                    consistency = 1.0

                w_candidates = [
                    uniq
                    for k, uniq in enumerate(unique)
                    if k != i
                    and k != j
                    and uniq["num"] < id_c["num"]
                    and uniq["num"] >= od_c["num"] * 0.05
                ]
                if w_candidates:
                    expected_w = (od_c["num"] - id_c["num"]) / 2.0
                    if expected_w > 0:
                        radial_cands = [
                            candidate
                            for candidate in w_candidates
                            if abs(candidate["num"] - expected_w) / expected_w <= 0.5
                        ]
                        if radial_cands:
                            radial_cands.sort(
                                key=lambda candidate: abs(candidate["num"] - expected_w)
                            )
                            w_candidates = radial_cands
                        else:
                            w_candidates.sort(
                                key=lambda candidate: candidate["num"],
                                reverse=True,
                            )
                    else:
                        w_candidates.sort(
                            key=lambda candidate: candidate["num"],
                            reverse=True,
                        )
                w_c = w_candidates[0] if w_candidates else None

                magnitude_score = od_c["num"] / max_val
                score = magnitude_score * 1.5
                score += max(0, 1.0 - consistency * 3) * 0.5
                if w_c and id_c["num"] > w_c["num"]:
                    score += 0.2
                if re.match(r"^[ØøΦ⌀∅]", od_c["value"]):
                    score += 0.3
                if re.match(r"^[ØøΦ⌀∅]", id_c["value"]):
                    score += 0.2

                logger.info(
                    f"  조합 OD={od_c['value']}({scale_od:.2f}) "
                    f"ID={id_c['value']}({scale_id:.2f}) "
                    f"일관성={consistency:.3f} 크기={magnitude_score:.2f} "
                    f"점수={score:.2f}"
                )

                if score > best_score:
                    best_score = score
                    best_combo = (od_c, id_c, w_c)

    if best_combo and best_score > 0.3:
        od, id_val, w = best_combo
        logger.info(
            f"스케일 검증 선택: OD={od['value']}, ID={id_val['value']}, "
            f"W={w['value'] if w else 'N/A'} (점수={best_score:.2f})"
        )
    else:
        logger.info(f"스케일 검증 실패 (best={best_score:.2f}) → 크기 순서 폴백")
        valid = [uniq for uniq in unique if uniq["num"] >= 30]
        if len(valid) >= 3:
            od = valid[0]
            id_val = valid[1]
            w = valid[2]
        elif len(valid) == 2:
            od = valid[0]
            ratio = valid[1]["num"] / valid[0]["num"] if valid[0]["num"] > 0 else 0
            if ratio > 0.5:
                id_val = valid[1]
            else:
                w = valid[1]
        elif len(unique) == 1:
            od = unique[0]

    return {
        "od": _fmt(od),
        "id": _fmt(id_val),
        "w": _fmt(w),
        "rois": [],
        "debug": {
            "candidates": len(candidates),
            "unique": len(unique),
            "total_dims": len(dims),
            "values": [(candidate["value"], candidate["num"]) for candidate in unique],
            "scale_score": round(best_score, 3),
            "dia_outer_px": dia_outer_px,
            "dia_inner_px": dia_inner_px,
        },
    }


def _fmt(candidate: Optional[Dict]) -> Optional[Dict]:
    """후보를 결과 형식으로 변환."""
    if not candidate:
        return None
    return {
        "value": candidate["value"],
        "confidence": candidate["confidence"],
        "bbox": candidate["bbox"],
    }
