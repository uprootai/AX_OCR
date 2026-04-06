"""Shared helpers for dimension ensemble orchestration."""

import re
from typing import Dict, List, Optional

import numpy as np


def _extract_num(val_str: Optional[str]) -> Optional[float]:
    """'Ø1036' → 1036.0, '550+2' → 550.0, 'Ø838.2.00' → 838.2, None → None."""
    if val_str is None:
        return None
    cleaned = re.sub(r"[ØøΦ⌀∅()R]", "", str(val_str))
    m = re.search(r"(\d+\.?\d*)", cleaned)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            return None
    return None


def _apply_soft_filter(result: Dict, drawing_title: str = "") -> Dict:
    """비베어링/이상치 soft 필터 — confidence penalty 적용."""
    penalties = []
    confidence = 1.0
    od_num = _extract_num(result.get("od", {}).get("value"))
    id_num = _extract_num(result.get("id", {}).get("value"))
    w_num = _extract_num(result.get("w", {}).get("value"))

    title_upper = drawing_title.upper()
    if not any(kw in title_upper for kw in ("BEARING", "BRG", "베어링")):
        confidence *= 0.85
        penalties.append("title_missing_bearing")

    if od_num is not None and (od_num < 50 or od_num > 2000):
        confidence *= 0.80
        penalties.append("od_out_of_range")

    if od_num and id_num and od_num <= id_num:
        confidence *= 0.75
        penalties.append("invalid_physical_order")
    if id_num and w_num and id_num <= w_num:
        confidence *= 0.85
        penalties.append("id_leq_w")

    result["soft_filter"] = {
        "confidence": round(confidence, 2),
        "applied_penalties": penalties,
        "drawing_title": drawing_title,
    }
    return result


def _vote_best(values: List[Optional[float]], tolerance: float = 5.0) -> Optional[float]:
    """가장 빈번한 값 선택 (±tolerance 이내 동일 취급)."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    groups: List[List[float]] = []
    for value in sorted(valid):
        placed = False
        for group in groups:
            if abs(value - group[0]) <= tolerance:
                group.append(value)
                placed = True
                break
        if not placed:
            groups.append([value])
    best = max(groups, key=len)
    return round(sum(best) / len(best), 1)


def _parse_circle_str(raw) -> Optional[tuple]:
    """numpy str '[1008 1146  810]' → (1008, 1146, 810)."""
    if raw is None:
        return None
    if isinstance(raw, (tuple, list)) and len(raw) >= 3:
        return tuple(int(x) for x in raw[:3])
    if isinstance(raw, np.ndarray) and len(raw) >= 3:
        return tuple(int(x) for x in raw[:3])
    if isinstance(raw, str):
        arr = np.fromstring(raw.strip("[]"), sep=" ")
        if len(arr) >= 3:
            return tuple(int(x) for x in arr[:3])
    return None


def _run_s06_yolo_ocr(image_path: str, model_path: str) -> Dict:
    """S06: YOLO 텍스트 검출 → PaddleOCR 읽기 → 규칙 분류."""
    from services.s06_yolo_ocr import run_s06_yolo_ocr

    return run_s06_yolo_ocr(image_path, model_path)
