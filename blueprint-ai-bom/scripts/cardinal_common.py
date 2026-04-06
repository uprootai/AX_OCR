#!/usr/bin/env python3
"""Shared helpers for Cardinal projection experiment scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
BLUEPRINT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = BLUEPRINT_ROOT.parent
DEFAULT_OUT_DIR = Path(
    os.environ.get(
        "AX_GT_VALIDATION_OUT_DIR",
        str(
            PROJECT_ROOT
            / "docs-site-starlight"
            / "public"
            / "images"
            / "gt-validation"
            / "steps"
        ),
    )
)
DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_R_RATIO = 0.08
MAX_R_RATIO = 0.48
AUXILIARY_SEARCH_TOP_MARGIN = 80
AUXILIARY_SEARCH_BOTTOM_MARGIN = 20
AUXILIARY_SEARCH_X_LEFT_RATIO = 0.20
AUXILIARY_SEARCH_X_RIGHT_RATIO = 1.40
AUXILIARY_SEARCH_BOTTOM_RATIO = 0.45
AUXILIARY_SMOOTH_WINDOW = 7
AUXILIARY_KERNEL_RATIO = 0.08
AUXILIARY_MIN_ROW_SCORE_RATIO = 0.03
AUXILIARY_MIN_ROW_SCORE = 12.0
AUXILIARY_PEAK_DISTANCE = 18
AUXILIARY_MAX_LINES = 3
SECTION_SEARCH_TOP_RATIO = 0.05
SECTION_SEARCH_BOTTOM_RATIO = 0.80
SECTION_SEARCH_X_MARGIN_RATIO = 0.01
SECTION_SEARCH_LEFT_OVERLAP_RADIUS_RATIO = 0.45
SECTION_SEARCH_TOP_RADIUS_RATIO = 0.65
SECTION_SEARCH_BOTTOM_RADIUS_RATIO = 1.45
SECTION_BAND_SMOOTH_RATIO = 0.02
SECTION_BAND_MIN_SCORE_RATIO = 0.18
SECTION_BAND_MIN_SEGMENT_RATIO = 0.04
SECTION_BAND_MIN_WIDTH_RATIO = 0.15
SECTION_BAND_LEFT_PADDING_MIN = 120
SECTION_BAND_LEFT_PADDING_RATIO = 0.80
SECTION_BAND_RIGHT_PADDING_MIN = 220
SECTION_BAND_RIGHT_PADDING_RATIO = 1.10
SECTION_SMOOTH_WINDOW = 9
SECTION_HORIZONTAL_KERNEL_RATIO = 0.18
SECTION_VERTICAL_KERNEL_RATIO = 0.10
SECTION_MIN_PEAK_SCORE = 12.0
SECTION_MIN_ROW_SCORE_RATIO = 0.05
SECTION_MIN_COL_SCORE_RATIO = 0.05
SECTION_MIN_ROW_RELATIVE_RATIO = 0.45
SECTION_MIN_COL_RELATIVE_RATIO = 0.35
SECTION_ROW_PEAK_DISTANCE_RATIO = 0.04
SECTION_COL_PEAK_DISTANCE_RATIO = 0.10
SECTION_MAX_HORIZONTAL_LINES = 3
SECTION_MAX_VERTICAL_LINES = 3
SECTION_EDGE_WINDOW_RATIO = 0.12
SECTION_EDGE_PEAK_MIN_SCORE_RATIO = 0.70
SECTION_EDGE_PEAK_MIN_SEPARATION = 36
SECTION_EDGE_EXTRA_VERTICAL_LINES = 2
SECTION_TOP_EDGE_WINDOW_RATIO = 0.12
SECTION_TOP_EDGE_MIN_SCORE_RATIO = 0.45
SECTION_TOP_EDGE_MIN_SEPARATION = 48
SECTION_TOP_EDGE_EXTRA_HORIZONTAL_LINES = 1
SECTION_OUTER_SEARCH_RATIO = 0.45
SECTION_OUTER_PEAK_MIN_SCORE_RATIO = 0.55
SECTION_OUTER_PEAK_DISTANCE_RATIO = 0.04
SECTION_OUTER_MAX_VERTICAL_LINES = 2
OCR_API = os.environ.get("PADDLEOCR_API_URL", "http://localhost:5006/api/v1/ocr")


def run_ocr(image_path: str | Path, timeout: int = 120) -> list[dict[str, Any]]:
    image_file = Path(image_path)
    if not image_file.exists():
        return []

    mime_type = "image/png" if image_file.suffix.lower() == ".png" else "image/jpeg"
    try:
        with image_file.open("rb") as file_obj:
            response = requests.post(
                OCR_API,
                files={"file": (image_file.name, file_obj, mime_type)},
                timeout=timeout,
            )
        response.raise_for_status()
        return response.json().get("detections", [])
    except Exception as exc:
        print(f"  ⚠ OCR failed for {image_file.name}: {exc}")
        return []


def normalized_region_to_bounds(
    region: dict[str, float] | None,
    width: int,
    height: int,
) -> tuple[int, int, int, int] | None:
    if not region:
        return None

    x1 = int(np.clip(round(float(region.get("left", 0.0)) * width), 0, width - 1))
    y1 = int(np.clip(round(float(region.get("top", 0.0)) * height), 0, height - 1))
    x2 = int(np.clip(round(float(region.get("right", 1.0)) * width), x1 + 1, width))
    y2 = int(np.clip(round(float(region.get("bottom", 1.0)) * height), y1 + 1, height))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def detect_section_view_bounds(
    gray: np.ndarray,
    image_path: str | Path | None = None,
    ocr_dets: list[dict[str, Any]] | None = None,
) -> tuple[tuple[int, int, int, int] | None, list[dict[str, Any]], dict[str, dict[str, float]]]:
    if image_path is None and ocr_dets is None:
        return None, [], {}

    if ocr_dets is None and image_path is not None:
        ocr_dets = run_ocr(image_path)
    ocr_dets = ocr_dets or []

    backend_path = str(BLUEPRINT_ROOT / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from services.dimension_ensemble import _detect_drawing_views

    height, width = gray.shape[:2]
    views = _detect_drawing_views(
        ocr_dets,
        width,
        height,
        str(image_path) if image_path is not None else "",
    )
    return normalized_region_to_bounds(views.get("section_view"), width, height), ocr_dets, views


def get_font(size: int = 16) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_header(
    img_bgr: np.ndarray,
    title: str,
    subtitle: str = "",
    subtitle2: str = "",
    *,
    title_min_font: int = 16,
    title_divisor: int = 60,
    subtitle_min_font: int = 12,
    subtitle_divisor: int = 80,
    bar_h_no_sub2: int = 60,
    bar_h_with_sub2: int = 80,
    subtitle_y: int = 30,
    subtitle2_y: int = 52,
) -> Image.Image:
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    height, width = img_bgr.shape[:2]
    font = get_font(max(title_min_font, height // title_divisor))
    font_sm = get_font(max(subtitle_min_font, height // subtitle_divisor))
    bar_h = bar_h_with_sub2 if subtitle2 else bar_h_no_sub2
    draw.rectangle([0, 0, width, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if subtitle:
        draw.text((10, subtitle_y), subtitle, fill="#AAAAAA", font=font_sm)
    if subtitle2:
        draw.text((10, subtitle2_y), subtitle2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(
    pil_img: Image.Image,
    name: str,
    max_w: int = 1400,
    *,
    out_dir: Path | None = None,
    quality: int = 85,
    show_size: bool = False,
) -> None:
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize(
            (max_w, int(pil_img.height * ratio)),
            Image.LANCZOS,
        )

    target_dir = out_dir or DEFAULT_OUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / name
    pil_img.save(out_path, quality=quality)
    suffix = f" ({pil_img.width}x{pil_img.height})" if show_size else ""
    print(f"  ✓ {name}{suffix}")


def find_main_view_region(gray: np.ndarray) -> tuple[int, int, int, int]:
    height, width = gray.shape
    x1, x2 = 0, int(width * 0.55)
    y1, y2 = int(height * 0.10), int(height * 0.90)
    return x1, y1, x2, y2


def smooth_signal(values: np.ndarray, window_size: int) -> np.ndarray:
    if window_size <= 1 or len(values) == 0:
        return values.astype(np.float32)
    kernel = np.ones(window_size, dtype=np.float32) / float(window_size)
    return np.convolve(values, kernel, mode="same")


def select_peak_indices(
    scores: np.ndarray,
    min_score: float,
    peak_distance: int,
    max_lines: int,
) -> list[int]:
    selected_indices = []
    for idx in np.argsort(scores)[::-1]:
        idx = int(idx)
        if scores[idx] < min_score:
            break
        if any(abs(idx - prev_idx) <= peak_distance for prev_idx in selected_indices):
            continue
        selected_indices.append(idx)
        if len(selected_indices) >= max_lines:
            break
    selected_indices.sort()
    return selected_indices


def find_dense_axis_segments(
    scores: np.ndarray,
    min_score: float,
    min_span: int,
) -> list[tuple[int, int]]:
    active_mask = scores >= min_score
    segments = []
    start_idx = None

    for idx, is_active in enumerate(active_mask):
        if is_active and start_idx is None:
            start_idx = idx
            continue
        if is_active or start_idx is None:
            continue
        if idx - start_idx >= min_span:
            segments.append((start_idx, idx))
        start_idx = None

    if start_idx is not None and len(scores) - start_idx >= min_span:
        segments.append((start_idx, len(scores)))

    return segments


def detect_concentric_alt(
    gray: np.ndarray,
    min_r: int,
    max_r: int,
) -> list[tuple[float, float, float]]:
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles = []
    hc = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT_ALT,
        dp=1.5,
        minDist=20,
        param1=150,
        param2=0.85,
        minRadius=min_r,
        maxRadius=max_r,
    )
    if hc is not None:
        for cx, cy, radius in hc[0]:
            circles.append((float(cx), float(cy), float(radius)))
    return circles


def select_primary_concentric_circles(
    circles: list[tuple[float, float, float]],
    center_tol: int = 12,
    radius_tol: int = 8,
    max_count: int = 3,
) -> list[tuple[float, float, float]]:
    if not circles:
        return []

    groups = []
    for circle in sorted(circles, key=lambda item: item[2], reverse=True):
        cx, cy, radius = circle
        matched = False
        for group in groups:
            gcx, gcy = group["center"]
            if abs(cx - gcx) <= center_tol and abs(cy - gcy) <= center_tol:
                group["circles"].append(circle)
                matched = True
                break
        if not matched:
            groups.append({"center": (cx, cy), "circles": [circle]})

    groups.sort(
        key=lambda group: (
            len(group["circles"]),
            max(item[2] for item in group["circles"]),
        ),
        reverse=True,
    )

    deduped = []
    for circle in sorted(groups[0]["circles"], key=lambda item: item[2]):
        if deduped and abs(circle[2] - deduped[-1][2]) < radius_tol:
            continue
        deduped.append(circle)

    if len(deduped) <= max_count:
        return deduped

    pick_idx = np.linspace(0, len(deduped) - 1, max_count).round().astype(int)
    return [deduped[idx] for idx in pick_idx]


def find_auxiliary_projection_rows(
    gray: np.ndarray,
    rx1: int,
    ry1: int,
    rx2: int,
    center_full: tuple[float, float] | None,
    outer_r: float | None,
) -> tuple[list[int], tuple[int, int, int, int] | None]:
    if center_full is None or outer_r is None:
        return [], None

    gray_h, gray_w = gray.shape
    center_x, center_y = center_full
    search_x1 = int(
        max(0, min(rx1, center_x - outer_r * AUXILIARY_SEARCH_X_LEFT_RATIO))
    )
    search_x2 = int(
        min(gray_w, max(rx2, center_x + outer_r * AUXILIARY_SEARCH_X_RIGHT_RATIO))
    )
    search_y1 = max(0, int(ry1 - AUXILIARY_SEARCH_TOP_MARGIN))
    search_y2 = int(
        min(
            gray_h,
            max(search_y1 + 1, center_y - outer_r * AUXILIARY_SEARCH_BOTTOM_RATIO),
        )
    )
    search_y2 = max(search_y1 + 1, min(search_y2, ry1 - AUXILIARY_SEARCH_BOTTOM_MARGIN))
    if search_y2 <= search_y1 or search_x2 <= search_x1:
        return [], None

    roi = gray[search_y1:search_y2, search_x1:search_x2]
    _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel_width = max(5, int((search_x2 - search_x1) * AUXILIARY_KERNEL_RATIO))
    if kernel_width % 2 == 0:
        kernel_width += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
    emphasized = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    row_scores = emphasized.sum(axis=1).astype(np.float32) / 255.0
    smoothed_scores = smooth_signal(row_scores, AUXILIARY_SMOOTH_WINDOW)
    min_score = max(
        AUXILIARY_MIN_ROW_SCORE,
        float(smoothed_scores.max()) * AUXILIARY_MIN_ROW_SCORE_RATIO,
    )
    selected_indices = select_peak_indices(
        smoothed_scores,
        min_score,
        AUXILIARY_PEAK_DISTANCE,
        AUXILIARY_MAX_LINES,
    )
    rows = [search_y1 + idx for idx in selected_indices]
    return rows, (search_x1, search_y1, search_x2, search_y2)


def find_section_projection_peaks(
    gray: np.ndarray,
    section_bounds: tuple[int, int, int, int] | None,
) -> tuple[list[int], list[int], tuple[int, int, int, int] | None]:
    if section_bounds is None:
        return [], [], None

    gray_h, gray_w = gray.shape
    sx1, sy1, sx2, sy2 = section_bounds
    section_width = max(1, sx2 - sx1)
    section_height = max(1, sy2 - sy1)

    section_x1 = max(0, int(sx1 - section_width * SECTION_SEARCH_LEFT_OVERLAP_RADIUS_RATIO))
    section_x2 = min(gray_w, int(sx2 + section_width * SECTION_SEARCH_X_MARGIN_RATIO))
    section_y1 = max(0, int(sy1 - section_height * SECTION_SEARCH_TOP_RATIO))
    section_y2 = min(gray_h, int(sy2 + section_height * SECTION_SEARCH_BOTTOM_RATIO))
    if section_x2 <= section_x1 or section_y2 <= section_y1:
        return [], [], section_bounds

    roi = gray[section_y1:section_y2, section_x1:section_x2]
    _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    horizontal_kernel_w = max(5, int((section_x2 - section_x1) * SECTION_HORIZONTAL_KERNEL_RATIO))
    vertical_kernel_h = max(5, int((section_y2 - section_y1) * SECTION_VERTICAL_KERNEL_RATIO))
    if horizontal_kernel_w % 2 == 0:
        horizontal_kernel_w += 1
    if vertical_kernel_h % 2 == 0:
        vertical_kernel_h += 1

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_kernel_w, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_kernel_h))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

    row_scores = smooth_signal(
        horizontal.sum(axis=1).astype(np.float32) / 255.0,
        SECTION_SMOOTH_WINDOW,
    )
    col_scores = smooth_signal(
        vertical.sum(axis=0).astype(np.float32) / 255.0,
        SECTION_SMOOTH_WINDOW,
    )

    row_min_score = max(
        SECTION_MIN_PEAK_SCORE,
        float(row_scores.max()) * SECTION_MIN_ROW_SCORE_RATIO,
    )
    col_min_score = max(
        SECTION_MIN_PEAK_SCORE,
        float(col_scores.max()) * SECTION_MIN_COL_SCORE_RATIO,
    )

    row_peak_distance = max(1, int(section_height * SECTION_ROW_PEAK_DISTANCE_RATIO))
    col_peak_distance = max(1, int(section_width * SECTION_COL_PEAK_DISTANCE_RATIO))
    row_indices = select_peak_indices(
        row_scores,
        row_min_score,
        row_peak_distance,
        SECTION_MAX_HORIZONTAL_LINES,
    )
    col_indices = select_peak_indices(
        col_scores,
        col_min_score,
        col_peak_distance,
        SECTION_MAX_VERTICAL_LINES,
    )

    row_segments = find_dense_axis_segments(
        row_scores,
        max(
            row_min_score * SECTION_MIN_ROW_RELATIVE_RATIO,
            float(row_scores.max()) * SECTION_BAND_MIN_SCORE_RATIO,
        ),
        max(1, int(section_height * SECTION_BAND_MIN_SEGMENT_RATIO)),
    )
    if row_segments:
        row_start = min(segment[0] for segment in row_segments)
        row_end = max(segment[1] for segment in row_segments)
        band_height = row_end - row_start
        if band_height >= section_height * SECTION_BAND_MIN_WIDTH_RATIO:
            top_padding = max(
                SECTION_BAND_LEFT_PADDING_MIN,
                int(section_height * SECTION_BAND_LEFT_PADDING_RATIO),
            )
            bottom_padding = max(
                SECTION_BAND_RIGHT_PADDING_MIN,
                int(section_height * SECTION_BAND_RIGHT_PADDING_RATIO),
            )
            section_y1 = max(0, section_y1 + row_start - top_padding)
            section_y2 = min(gray_h, section_y1 + band_height + top_padding + bottom_padding)

    col_segments = find_dense_axis_segments(
        col_scores,
        max(
            col_min_score * SECTION_MIN_COL_RELATIVE_RATIO,
            float(col_scores.max()) * SECTION_BAND_MIN_SCORE_RATIO,
        ),
        max(1, int(section_width * SECTION_BAND_MIN_SEGMENT_RATIO)),
    )
    if col_segments:
        left_edge = min(segment[0] for segment in col_segments)
        right_edge = max(segment[1] for segment in col_segments)
        band_width = right_edge - left_edge
        if band_width >= section_width * SECTION_BAND_MIN_WIDTH_RATIO:
            left_padding = max(
                SECTION_BAND_LEFT_PADDING_MIN,
                int(section_width * SECTION_BAND_LEFT_PADDING_RATIO),
            )
            right_padding = max(
                SECTION_BAND_RIGHT_PADDING_MIN,
                int(section_width * SECTION_BAND_RIGHT_PADDING_RATIO),
            )
            section_x1 = max(0, section_x1 + left_edge - left_padding)
            section_x2 = min(gray_w, section_x1 + band_width + left_padding + right_padding)

    section_bounds = (section_x1, section_y1, section_x2, section_y2)
    roi = gray[section_y1:section_y2, section_x1:section_x2]
    _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    row_scores = smooth_signal(
        horizontal.sum(axis=1).astype(np.float32) / 255.0,
        SECTION_SMOOTH_WINDOW,
    )
    col_scores = smooth_signal(
        vertical.sum(axis=0).astype(np.float32) / 255.0,
        SECTION_SMOOTH_WINDOW,
    )

    row_min_score = max(
        SECTION_MIN_PEAK_SCORE,
        float(row_scores.max()) * SECTION_MIN_ROW_SCORE_RATIO,
    )
    col_min_score = max(
        SECTION_MIN_PEAK_SCORE,
        float(col_scores.max()) * SECTION_MIN_COL_SCORE_RATIO,
    )

    row_indices = select_peak_indices(
        row_scores,
        row_min_score,
        max(1, int((section_y2 - section_y1) * SECTION_ROW_PEAK_DISTANCE_RATIO)),
        SECTION_MAX_HORIZONTAL_LINES,
    )
    col_indices = select_peak_indices(
        col_scores,
        col_min_score,
        max(1, int((section_x2 - section_x1) * SECTION_COL_PEAK_DISTANCE_RATIO)),
        SECTION_MAX_VERTICAL_LINES,
    )

    edge_window_w = max(1, int((section_x2 - section_x1) * SECTION_EDGE_WINDOW_RATIO))
    edge_window_h = max(1, int((section_y2 - section_y1) * SECTION_TOP_EDGE_WINDOW_RATIO))

    local_col_scores = col_scores.copy()
    if local_col_scores.size > 0:
        mask_width = max(1, min(local_col_scores.size, edge_window_w))
        local_col_scores[:-mask_width] = 0.0
    right_edge_candidates = []
    for existing_idx in col_indices:
        if local_col_scores.size == 0:
            break
        mask_start = max(0, existing_idx - SECTION_EDGE_PEAK_MIN_SEPARATION)
        mask_end = min(
            local_col_scores.size,
            existing_idx + SECTION_EDGE_PEAK_MIN_SEPARATION + 1,
        )
        local_col_scores[mask_start:mask_end] = 0.0
    if local_col_scores.size > 0:
        local_idx = int(np.argmax(local_col_scores))
        if (
            float(col_scores[local_idx]) >= float(col_scores.max()) * SECTION_EDGE_PEAK_MIN_SCORE_RATIO
            and not any(
                abs(local_idx - existing_idx) < SECTION_EDGE_PEAK_MIN_SEPARATION
                for existing_idx in col_indices
            )
        ):
            right_edge_candidates.append(local_idx)
    if right_edge_candidates:
        col_indices = sorted(col_indices + right_edge_candidates[:SECTION_EDGE_EXTRA_VERTICAL_LINES])

    local_top_scores = row_scores.copy()
    if local_top_scores.size > 0:
        mask_height = max(1, min(local_top_scores.size, edge_window_h))
        local_top_scores[mask_height:] = 0.0
    top_edge_candidates = []
    top_edge_min_score = float(row_scores.max()) * SECTION_TOP_EDGE_MIN_SCORE_RATIO
    for existing_idx in row_indices:
        if local_top_scores.size == 0:
            break
        mask_start = max(0, existing_idx - SECTION_TOP_EDGE_MIN_SEPARATION)
        mask_end = min(
            local_top_scores.size,
            existing_idx + SECTION_TOP_EDGE_MIN_SEPARATION + 1,
        )
        local_top_scores[mask_start:mask_end] = 0.0
    if local_top_scores.size > 0:
        local_idx = int(np.argmax(local_top_scores))
        if (
            float(row_scores[local_idx]) >= top_edge_min_score
            and not any(
                abs(local_idx - existing_idx) < SECTION_TOP_EDGE_MIN_SEPARATION
                for existing_idx in row_indices
            )
        ):
            top_edge_candidates.append(local_idx)
    if top_edge_candidates:
        row_indices = sorted(row_indices + top_edge_candidates[:SECTION_TOP_EDGE_EXTRA_HORIZONTAL_LINES])

    horizontal_rows = [section_y1 + idx for idx in row_indices]
    vertical_cols = [section_x1 + idx for idx in col_indices]

    return vertical_cols, horizontal_rows, section_bounds


def cardinal_max_scan(
    gray: np.ndarray,
    cx: float,
    cy: float,
    outer_r: float,
    max_scan_r: int | None = None,
    sweep_px: int = 30,
) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:
    height, width = gray.shape
    if max_scan_r is None:
        max_scan_r = int(outer_r * 1.3)

    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    solid = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    directions = [
        ("N", 0, -1),
        ("S", 0, 1),
        ("E", 1, 0),
        ("W", -1, 0),
    ]
    angle_map = {"E": 0, "S": 90, "W": 180, "N": 270}

    radial_profile = []
    outer_boundary_r = int(np.ceil(outer_r))
    sweep_span = sweep_px * 2 + 1
    major_density_px = max(3, int(round(sweep_span * 0.08)))
    outside_empty_stop_px = 10
    density_drop_stop_px = 10

    def axis_density_profile(dx: int, dy: int) -> np.ndarray:
        density = np.zeros(max_scan_r, dtype=np.int32)
        for r_px in range(1, max_scan_r):
            solid_hits = 0
            for offset in range(-sweep_px, sweep_px + 1):
                if dx == 0:
                    px = int(cx + offset)
                    py = int(cy + r_px * dy)
                else:
                    px = int(cx + r_px * dx)
                    py = int(cy + offset)
                if 0 <= px < width and 0 <= py < height and solid[py, px] > 0:
                    solid_hits += 1
            density[r_px] = solid_hits
        return density

    def pick_vertical_radius(density_profile: np.ndarray) -> int:
        entered_solid = False
        initial_empty = 0
        low_density_run = 0
        peak_density = 0
        best_vertical_r = outer_boundary_r

        for r_px in range(outer_boundary_r, max_scan_r):
            density = int(density_profile[r_px])

            if not entered_solid:
                if density >= major_density_px:
                    entered_solid = True
                    peak_density = density
                    best_vertical_r = r_px
                    initial_empty = 0
                    continue

                if density == 0:
                    initial_empty += 1
                    if initial_empty >= outside_empty_stop_px:
                        return outer_boundary_r
                else:
                    initial_empty = 0
                continue

            peak_density = max(peak_density, density)
            strong_density_px = max(major_density_px, int(round(peak_density * 0.25)))
            weak_density_px = max(1, int(round(peak_density * 0.15)))

            if density >= strong_density_px:
                best_vertical_r = r_px
                low_density_run = 0
            elif density <= weak_density_px:
                low_density_run += 1
                if low_density_run >= density_drop_stop_px:
                    break
            else:
                low_density_run = 0

        return best_vertical_r

    for dir_name, dx, dy in directions:
        best_r = 0
        best_x, best_y = int(cx), int(cy)

        if dx == 0:
            density_profile = axis_density_profile(dx, dy)
            best_r = pick_vertical_radius(density_profile)
            best_x = int(round(cx))
            best_y = int(round(cy + best_r * dy))
            radial_profile.append((angle_map[dir_name], best_r, best_x, best_y))
            print(
                f"    {dir_name}: max_r={best_r} ({best_x},{best_y})"
                f"{' ← 돌출' if best_r > outer_r * 1.05 else ''}"
            )
            continue

        for offset in range(-sweep_px, sweep_px + 1):
            scan_r = 0
            scan_x, scan_y = int(cx), int(cy)
            consecutive_empty = 0

            for r_px in range(1, max_scan_r):
                px = int(cx + r_px * dx)
                py = int(cy + offset)

                if 0 <= px < width and 0 <= py < height:
                    if solid[py, px] > 0:
                        actual_r = int(round(abs(px - cx)))
                        if actual_r > scan_r:
                            scan_r = actual_r
                            scan_x, scan_y = px, py
                        consecutive_empty = 0
                    else:
                        consecutive_empty += 1
                        if consecutive_empty > 30 and scan_r > outer_r:
                            break
                else:
                    break

            if scan_r > best_r:
                best_r = scan_r
                best_x, best_y = scan_x, scan_y

        radial_profile.append((angle_map[dir_name], best_r, best_x, best_y))
        print(
            f"    {dir_name}: max_r={best_r} ({best_x},{best_y})"
            f"{' ← 돌출' if best_r > outer_r * 1.05 else ''}"
        )

    threshold = outer_r * 1.05
    protrusions = [item for item in radial_profile if item[1] > threshold]
    return radial_profile, protrusions


def collect_projection_data(
    gray: np.ndarray,
    image_path: str | Path | None = None,
    ocr_dets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    section_bounds, section_ocr_dets, detected_views = detect_section_view_bounds(
        gray,
        image_path=image_path,
        ocr_dets=ocr_dets,
    )

    height, width = gray.shape
    main_view_norm = (detected_views or {}).get("main_view")
    if main_view_norm and isinstance(main_view_norm, dict):
        rx1 = int(main_view_norm.get("left", 0) * width)
        ry1 = int(main_view_norm.get("top", 0.10) * height)
        rx2 = int(main_view_norm.get("right", 0.55) * width)
        ry2 = int(main_view_norm.get("bottom", 0.90) * height)
    else:
        rx1, ry1, rx2, ry2 = find_main_view_region(gray)

    roi_gray = gray[ry1:ry2, rx1:rx2]
    roi_h, roi_w = roi_gray.shape
    min_r = int(min(roi_h, roi_w) * MIN_R_RATIO)
    max_r = int(min(roi_h, roi_w) * MAX_R_RATIO)

    raw_circles_roi = detect_concentric_alt(roi_gray, min_r, max_r)
    circles_roi = select_primary_concentric_circles(raw_circles_roi)
    circles_full = [(cx + rx1, cy + ry1, radius) for cx, cy, radius in circles_roi]

    peaks_full = []
    outer_r = None
    center_full = None
    auxiliary_rows = []
    auxiliary_bounds = None
    section_vertical_cols = []
    section_horizontal_rows = []
    if circles_roi:
        outer_r = max(circle[2] for circle in circles_roi)
        ccx_roi, ccy_roi = circles_roi[0][0], circles_roi[0][1]
        center_full = (circles_full[0][0], circles_full[0][1])
        _, protrusions_roi = cardinal_max_scan(roi_gray, ccx_roi, ccy_roi, outer_r)
        peaks_full = [
            (angle_deg, max_radius, px + rx1, py + ry1)
            for angle_deg, max_radius, px, py in protrusions_roi
        ]
        auxiliary_rows, auxiliary_bounds = find_auxiliary_projection_rows(
            gray,
            rx1,
            ry1,
            rx2,
            center_full,
            outer_r,
        )
        section_vertical_cols, section_horizontal_rows, section_bounds = find_section_projection_peaks(
            gray,
            section_bounds,
        )

    return {
        "main_view_region": (rx1, ry1, rx2, ry2),
        "raw_circles_roi": raw_circles_roi,
        "circles_full": circles_full,
        "peaks_full": peaks_full,
        "outer_r": outer_r,
        "center_full": center_full,
        "auxiliary_rows": auxiliary_rows,
        "auxiliary_bounds": auxiliary_bounds,
        "section_vertical_cols": section_vertical_cols,
        "section_horizontal_rows": section_horizontal_rows,
        "section_bounds": section_bounds,
        "ocr_dets": section_ocr_dets,
        "views": detected_views,
    }


def build_circle_lines(
    circles_full: list[tuple[float, float, float]],
) -> list[dict[str, object]]:
    dir_colors = {
        "N": (255, 100, 100),
        "S": (255, 100, 100),
        "E": (0, 200, 255),
        "W": (0, 200, 255),
    }
    lines = []
    for cx, cy, radius in circles_full:
        for dir_name, ddx, ddy, axis in [
            ("N", 0, -1, "h"),
            ("S", 0, 1, "h"),
            ("E", 1, 0, "v"),
            ("W", -1, 0, "v"),
        ]:
            px = int(round(cx + radius * ddx))
            py = int(round(cy + radius * ddy))
            lines.append(
                {
                    "px": px,
                    "py": py,
                    "axis": axis,
                    "color": dir_colors[dir_name],
                    "dir_name": dir_name,
                    "cx": float(cx),
                    "cy": float(cy),
                    "r": float(radius),
                }
            )
    return lines


def build_protrusion_lines(
    peaks_full: list[tuple[float, float, float, float]],
    center_full: tuple[float, float] | None,
    outer_r: float | None,
) -> list[dict[str, object]]:
    lines = []
    if not peaks_full or center_full is None or outer_r is None:
        return lines

    ccx, ccy = center_full
    for angle, _, ppx, ppy in peaks_full:
        for axis in ("h", "v"):
            lines.append(
                {
                    "px": int(ppx),
                    "py": int(ppy),
                    "axis": axis,
                    "color": (255, 0, 200),
                    "angle": angle,
                    "ccx": float(ccx),
                    "ccy": float(ccy),
                    "outer_r": float(outer_r),
                }
            )
    return lines


def build_auxiliary_lines(
    auxiliary_rows: list[int],
    center_full: tuple[float, float] | None,
    section_vertical_cols: list[int] | None = None,
    section_horizontal_rows: list[int] | None = None,
    section_bounds: tuple[int, int, int, int] | None = None,
) -> list[dict[str, object]]:
    section_vertical_cols = section_vertical_cols or []
    section_horizontal_rows = section_horizontal_rows or []
    if not auxiliary_rows and not section_vertical_cols and not section_horizontal_rows:
        return []

    anchor_x = 0 if center_full is None else int(round(center_full[0]))
    anchor_y = 0 if center_full is None else int(round(center_full[1]))
    if section_bounds is None:
        section_anchor_x = anchor_x
        section_anchor_y = anchor_y
    else:
        sx1, sy1, sx2, sy2 = section_bounds
        section_anchor_x = int(round((sx1 + sx2) / 2.0))
        section_anchor_y = int(round((sy1 + sy2) / 2.0))

    lines = [
        {
            "px": anchor_x,
            "py": int(round(py)),
            "axis": "h",
            "color": (255, 255, 0),
            "source": "auxiliary",
        }
        for py in auxiliary_rows
    ]
    lines.extend(
        {
            "px": int(round(px)),
            "py": section_anchor_y,
            "axis": "v",
            "color": (0, 255, 255),
            "source": "section",
        }
        for px in section_vertical_cols
    )
    lines.extend(
        {
            "px": section_anchor_x,
            "py": int(round(py)),
            "axis": "h",
            "color": (255, 200, 0),
            "source": "section",
        }
        for py in section_horizontal_rows
    )
    return lines


def draw_projection_lines_only(
    img: np.ndarray,
    circles_full: list[tuple[float, float, float]],
    circle_lines: list[dict[str, object]],
    peaks_full: list[tuple[float, float, float, float]],
    protrusion_lines: list[dict[str, object]],
    auxiliary_lines: list[dict[str, object]] | None = None,
) -> Image.Image:
    full_h, full_w = img.shape[:2]
    canvas = img.copy()
    auxiliary_lines = auxiliary_lines or []

    for cx, cy, radius in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(radius), (67, 160, 71), 4)

    circle_endpoint_color = (255, 255, 0)
    horizontal_color = (255, 255, 0)
    vertical_color = (0, 255, 255)
    protrusion_color = (255, 0, 200)

    for line in circle_lines:
        color = horizontal_color if line["axis"] == "h" else vertical_color
        if line["axis"] == "h":
            cv2.line(canvas, (0, int(line["py"])), (full_w, int(line["py"])), color, 2)
        else:
            cv2.line(canvas, (int(line["px"]), 0), (int(line["px"]), full_h), color, 2)
        cv2.circle(canvas, (int(line["px"]), int(line["py"])), 10, circle_endpoint_color, -1)
        cv2.circle(canvas, (int(line["px"]), int(line["py"])), 14, (60, 60, 60), 2)

    for line in protrusion_lines:
        if line["axis"] == "h":
            cv2.line(canvas, (0, int(line["py"])), (full_w, int(line["py"])), protrusion_color, 2)
        else:
            cv2.line(canvas, (int(line["px"]), 0), (int(line["px"]), full_h), protrusion_color, 2)

    for line in auxiliary_lines:
        color = tuple(line.get("color", horizontal_color if line["axis"] == "h" else vertical_color))
        if line["axis"] == "h":
            cv2.line(canvas, (0, int(line["py"])), (full_w, int(line["py"])), color, 2)
        else:
            cv2.line(canvas, (int(line["px"]), 0), (int(line["px"]), full_h), color, 2)

    for _, _, px, py in peaks_full:
        cv2.drawMarker(
            canvas,
            (int(px), int(py)),
            (0, 0, 255),
            cv2.MARKER_DIAMOND,
            28,
            3,
        )

    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
