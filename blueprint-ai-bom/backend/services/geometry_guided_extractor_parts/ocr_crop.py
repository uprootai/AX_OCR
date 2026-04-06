"""OCR crop helpers for geometry-guided dimension extraction."""

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _crop_ocr_around_circles(
    image_path: str,
    img_gray: np.ndarray,
    outer: np.ndarray,
    inner: Optional[np.ndarray],
    ocr_engine: str,
    confidence_threshold: float,
    orig_w: int,
    orig_h: int,
) -> tuple:
    """원 주변을 넓게 크롭하여 OCR."""
    import os
    import tempfile

    cx, cy, r = int(outer[0]), int(outer[1]), int(outer[2])

    from services.dimension_service import DimensionService

    dim_service = DimensionService()

    def _run_ocr_on_crop(crop_gray, offset_x, offset_y):
        if crop_gray.size == 0:
            return []
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            cv2.imwrite(tmp_path, crop_gray)
            result = dim_service.extract_dimensions(
                tmp_path,
                confidence_threshold,
                [ocr_engine],
            )
            found = result.get("dimensions", [])
            for dim in found:
                bbox = dim.get("bbox") if isinstance(dim, dict) else (
                    dim.bbox if hasattr(dim, "bbox") else None
                )
                if bbox:
                    if isinstance(bbox, dict):
                        bbox["x1"] += offset_x
                        bbox["y1"] += offset_y
                        bbox["x2"] += offset_x
                        bbox["y2"] += offset_y
                    else:
                        bbox.x1 += offset_x
                        bbox.y1 += offset_y
                        bbox.x2 += offset_x
                        bbox.y2 += offset_y
            return found
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    m1 = int(r * 1.8)
    c1_y1, c1_y2 = max(0, cy - m1), min(orig_h, cy + m1)
    c1_x1, c1_x2 = max(0, cx - m1), min(orig_w, cx + m1)

    c2_y1 = max(0, cy - int(r * 3.0))
    c2_y2 = min(orig_h, cy + int(r * 1.5))
    c2_x1 = max(0, cx - int(r * 2.0))
    c2_x2 = min(orig_w, cx + int(r * 2.0))

    x1, y1 = min(c1_x1, c2_x1), min(c1_y1, c2_y1)

    try:
        dims_focused = _run_ocr_on_crop(
            img_gray[c1_y1:c1_y2, c1_x1:c1_x2],
            c1_x1,
            c1_y1,
        )
        dims_wide = _run_ocr_on_crop(
            img_gray[c2_y1:c2_y2, c2_x1:c2_x2],
            c2_x1,
            c2_y1,
        )

        dims = list(dims_focused)
        existing_vals = {
            (dim.get("value", "") if isinstance(dim, dict) else dim.value)
            for dim in dims
        }
        for wide_dim in dims_wide:
            wide_value = wide_dim.get("value", "") if isinstance(wide_dim, dict) else wide_dim.value
            if wide_value not in existing_vals:
                dims.append(wide_dim)
                existing_vals.add(wide_value)

        for dim in dims:
            value = dim.get("value", "") if isinstance(dim, dict) else (
                dim.value if hasattr(dim, "value") else ""
            )
            bbox = dim.get("bbox", {}) if isinstance(dim, dict) else {}
            logger.info(f"  크롭OCR: val={value!r}  bbox={bbox}")
        logger.info(
            "크롭 OCR: "
            f"{len(dims)}개 치수 검출 "
            f"(focused={len(dims_focused)}, wide={len(dims_wide)})"
        )
        return dims, (x1, y1)
    except Exception as exc:
        logger.warning(f"크롭 OCR 실패: {exc}")
        return [], (0, 0)
