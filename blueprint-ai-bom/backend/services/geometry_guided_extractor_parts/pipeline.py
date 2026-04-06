"""Public pipeline entrypoints for geometry-guided dimension extraction."""

import logging
from typing import Dict

import cv2

from services.geometry_guided_extractor_parts import (
    circles as circles_module,
    classification as classification_module,
    ocr_crop as ocr_crop_module,
    rois as roi_module,
)

logger = logging.getLogger(__name__)


def extract_by_geometry(
    image_path: str,
    ocr_engine: str = "paddleocr",
    confidence_threshold: float = 0.3,
) -> Dict:
    """기하학 기반 OD/ID/W 추출."""
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {"error": "이미지 로드 실패"}

    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    circles_info = circles_module._detect_circles(img_gray, orig_w, orig_h)
    if not circles_info["found"]:
        return {
            "od": None,
            "id": None,
            "w": None,
            "circles": [],
            "dim_lines": [],
            "rois": [],
            "debug": {"error": "원/호 검출 실패", **circles_info},
        }

    outer_circle = circles_info["outer"]
    inner_circle = circles_info.get("inner")

    dim_lines = roi_module._detect_dimension_lines(
        img_gray,
        outer_circle,
        inner_circle,
        orig_w,
        orig_h,
    )

    crop_dims, crop_offset = ocr_crop_module._crop_ocr_around_circles(
        image_path,
        img_gray,
        outer_circle,
        inner_circle,
        ocr_engine,
        confidence_threshold,
        orig_w,
        orig_h,
    )

    result = classification_module._classify_by_circle_proximity(
        crop_dims,
        outer_circle,
        inner_circle,
        orig_w,
        orig_h,
    )

    result["circles"] = [
        {
            "cx": int(outer_circle[0]),
            "cy": int(outer_circle[1]),
            "r": int(outer_circle[2]),
            "role": "outer",
        }
    ]
    if inner_circle is not None:
        result["circles"].append(
            {
                "cx": int(inner_circle[0]),
                "cy": int(inner_circle[1]),
                "r": int(inner_circle[2]),
                "role": "inner",
            }
        )
    result["dim_lines"] = [
        {
            "x1": int(line["x1"]),
            "y1": int(line["y1"]),
            "x2": int(line["x2"]),
            "y2": int(line["y2"]),
            "direction": line["direction"],
        }
        for line in dim_lines
    ]

    return result


def get_geometry_supplementary_dims(
    image_path: str,
    ocr_engine: str = "paddleocr",
    confidence_threshold: float = 0.3,
) -> tuple:
    """원 검출 + 크롭 OCR로 보충 치수 목록 반환."""
    img_color = cv2.imread(image_path)
    if img_color is None:
        return [], None
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    orig_h, orig_w = img_gray.shape[:2]

    circles_info = circles_module._detect_circles(img_gray, orig_w, orig_h)
    if not circles_info["found"]:
        return [], None

    outer = circles_info["outer"]
    inner = circles_info.get("inner")
    r_outer = float(outer[2])

    crop_dims, _ = ocr_crop_module._crop_ocr_around_circles(
        image_path,
        img_gray,
        outer,
        inner,
        ocr_engine,
        confidence_threshold,
        orig_w,
        orig_h,
    )
    return crop_dims, r_outer
