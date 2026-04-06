#!/usr/bin/env python3
"""S08 Cardinal Projection v3 — 전체 도면에서 직선 투사

메인 뷰 크롭이 아닌 전체 도면에서:
1. 메인 뷰 영역에서 ALT 동심원 검출
2. 동서남북 4방향 최대치 스캔으로 돌출부 끝점 검출
3. 동심원/돌출부 끝점에서 전체 도면을 가로지르는 직선
4. SECTION 영역의 화살촉과 만나는지 확인
"""

import argparse
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from generate_protrusion_detect import cardinal_max_scan

SCRIPT_DIR = Path(__file__).resolve().parent
BLUEPRINT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = BLUEPRINT_ROOT.parent

SRC_DIR = Path(
    os.environ.get(
        "AX_DSE_BATCH_PNG_DIR",
        str(BLUEPRINT_ROOT / "data" / "dse_batch_test" / "converted_pngs"),
    )
)
OUT_DIR = Path(
    os.environ.get(
        "AX_GT_VALIDATION_OUT_DIR",
        str(PROJECT_ROOT / "docs-site-starlight" / "public" / "images" / "gt-validation" / "steps"),
    )
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

GT = {
    "TD0062015": {"name": "t1", "od": 360, "id": 190},
    "TD0062021": {"name": "t2", "od": 380, "id": 190},
    "TD0062031": {"name": "t4", "od": 420, "id": 260},
    "TD0062050": {"name": "t8", "od": 500, "id": 260},
}

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


def get_font(size=16):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_header(img_bgr, title, subtitle="", subtitle2=""):
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    h, w = img_bgr.shape[:2]
    font = get_font(max(16, h // 60))
    font_sm = get_font(max(12, h // 80))
    bar_h = 80 if subtitle2 else 60
    draw.rectangle([0, 0, w, bar_h], fill="#222222")
    draw.text((10, 5), title, fill="white", font=font)
    if subtitle:
        draw.text((10, 30), subtitle, fill="#AAAAAA", font=font_sm)
    if subtitle2:
        draw.text((10, 52), subtitle2, fill="#66BB6A", font=font_sm)
    return pil


def save_pil(pil_img, name, max_w=1400):
    if pil_img.width > max_w:
        ratio = max_w / pil_img.width
        pil_img = pil_img.resize(
            (max_w, int(pil_img.height * ratio)), Image.LANCZOS
        )
    out = OUT_DIR / name
    pil_img.save(out, quality=85)
    print(f"  ✓ {name} ({pil_img.width}x{pil_img.height})")


def find_main_view_region(gray):
    """콘텐츠 밀도 기반 메인 뷰 영역 추정

    전체 도면에서 좌측 ~55%가 정면도(메인 뷰) 영역.
    상하는 콘텐츠 밀도로 추정.
    """
    h, w = gray.shape
    # 좌측 55% = 메인 뷰 영역
    x1, x2 = 0, int(w * 0.55)
    # 상하 마진 10%
    y1, y2 = int(h * 0.10), int(h * 0.90)
    return x1, y1, x2, y2


def smooth_signal(values, window_size):
    if window_size <= 1 or len(values) == 0:
        return values.astype(np.float32)
    kernel = np.ones(window_size, dtype=np.float32) / float(window_size)
    return np.convolve(values, kernel, mode="same")


def select_peak_indices(scores, min_score, peak_distance, max_lines):
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


def find_dense_axis_segments(scores, min_score, min_span):
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


def detect_concentric_alt(gray_roi, min_r, max_r):
    """메인 뷰 ROI에서 ALT 동심원 검출"""
    blurred = cv2.GaussianBlur(gray_roi, (5, 5), 1.5)
    circles = []
    hc = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT_ALT, dp=1.5,
        minDist=20, param1=150, param2=0.85,
        minRadius=min_r, maxRadius=max_r,
    )
    if hc is not None:
        for cx, cy, r in hc[0]:
            circles.append((float(cx), float(cy), float(r)))
    return circles


def select_primary_concentric_circles(circles, center_tol=12, radius_tol=8, max_count=3):
    """같은 중심의 주 동심원 클러스터만 남긴다."""
    if not circles:
        return []

    groups = []
    for cx, cy, r in circles:
        matched_group = None
        for group in groups:
            gcx, gcy = group["center"]
            if np.hypot(cx - gcx, cy - gcy) <= center_tol:
                matched_group = group
                break
        if matched_group is None:
            groups.append({"center": (cx, cy), "circles": [(cx, cy, r)]})
            continue
        matched_group["circles"].append((cx, cy, r))
        xs = [item[0] for item in matched_group["circles"]]
        ys = [item[1] for item in matched_group["circles"]]
        matched_group["center"] = (float(np.mean(xs)), float(np.mean(ys)))

    groups.sort(
        key=lambda group: (
            len(group["circles"]),
            max(circle[2] for circle in group["circles"]),
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


def detect_arrowheads(gray):
    """S01 방식 — Black Hat 모폴로지로 실선 삼각형 화살촉만 검출

    Black Hat = closing - original → 작은 실선 구조(화살촉)만 강조.
    원본 이진화 컨투어와 달리 문자/해칭/볼트홀이 제거됨.
    """
    _, binary = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    ks = max(3, min(gray.shape[0], gray.shape[1]) // 150)
    ks = ks if ks % 2 == 1 else ks + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    black_hat = cv2.subtract(
        cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel), binary
    )

    dil_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    black_hat = cv2.dilate(black_hat, dil_k, iterations=1)

    contours, _ = cv2.findContours(
        black_hat, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    arrows = []
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
            acx, acy = x + w // 2, y + h // 2
        else:
            acx = int(M["m10"] / M["m00"])
            acy = int(M["m01"] / M["m00"])
        arrows.append({"x": float(acx), "y": float(acy), "area": float(area)})
    return arrows


def find_auxiliary_projection_rows(gray, rx1, ry1, rx2, center_full, outer_r):
    """상단 보조도 치수선이 모인 y 행을 찾아 추가 수평 투사선을 만든다."""
    if center_full is None or outer_r is None:
        return [], None

    h, w = gray.shape
    ccx, ccy = center_full
    circle_top_y = int(round(ccy - outer_r))
    search_y1 = max(AUXILIARY_SEARCH_TOP_MARGIN, ry1 - 70)
    search_y2 = min(
        circle_top_y - AUXILIARY_SEARCH_BOTTOM_MARGIN,
        int(ry1 + outer_r * AUXILIARY_SEARCH_BOTTOM_RATIO),
        int(h * 0.22),
    )
    search_x1 = max(rx1, int(round(ccx - outer_r * AUXILIARY_SEARCH_X_LEFT_RATIO)))
    search_x2 = min(rx2, int(round(ccx + outer_r * AUXILIARY_SEARCH_X_RIGHT_RATIO)))

    if search_y2 <= search_y1 or search_x2 <= search_x1:
        return [], None

    roi = gray[search_y1:search_y2, search_x1:search_x2]
    _, binary = cv2.threshold(
        roi,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    kernel_w = max(25, int(roi.shape[1] * AUXILIARY_KERNEL_RATIO))
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_w, 1))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    row_scores = horizontal.sum(axis=1).astype(np.float32) / 255.0
    smoothed_scores = smooth_signal(row_scores, AUXILIARY_SMOOTH_WINDOW)
    min_score = max(
        AUXILIARY_MIN_ROW_SCORE,
        roi.shape[1] * AUXILIARY_MIN_ROW_SCORE_RATIO,
    )
    selected_indices = select_peak_indices(
        smoothed_scores,
        min_score,
        AUXILIARY_PEAK_DISTANCE,
        AUXILIARY_MAX_LINES * 2,
    )
    rows = [search_y1 + idx for idx in selected_indices[:AUXILIARY_MAX_LINES]]
    return rows, (search_x1, search_y1, search_x2, search_y2)


def find_section_content_band(gray, rx2, center_full=None, outer_r=None):
    """메인 뷰 오른쪽에서 SECTION 단면도가 놓인 주요 x band를 찾는다."""
    h, w = gray.shape
    right_width = w - rx2
    search_x1 = min(w - 1, rx2 + max(20, int(w * SECTION_SEARCH_X_MARGIN_RATIO)))
    search_x2 = max(search_x1 + 1, w - max(20, int(w * 0.02)))
    search_y1 = max(0, int(h * SECTION_SEARCH_TOP_RATIO))
    search_y2 = max(search_y1 + 1, int(h * SECTION_SEARCH_BOTTOM_RATIO))

    if center_full is not None and outer_r is not None:
        _, ccy = center_full
        left_overlap = max(
            SECTION_BAND_LEFT_PADDING_MIN,
            int(round(outer_r * SECTION_SEARCH_LEFT_OVERLAP_RADIUS_RATIO)),
        )
        search_x1 = max(0, rx2 - left_overlap)
        search_y1 = max(0, int(round(ccy - outer_r * SECTION_SEARCH_TOP_RADIUS_RATIO)))
        search_y2 = min(h, int(round(ccy + outer_r * SECTION_SEARCH_BOTTOM_RADIUS_RATIO)))

    if search_x2 <= search_x1 or search_y2 <= search_y1:
        return None

    roi = gray[search_y1:search_y2, search_x1:search_x2]
    _, binary = cv2.threshold(
        roi,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    smooth_window = max(11, int(roi.shape[1] * SECTION_BAND_SMOOTH_RATIO))
    if smooth_window % 2 == 0:
        smooth_window += 1

    column_scores = smooth_signal(
        binary.sum(axis=0).astype(np.float32) / 255.0,
        smooth_window,
    )
    min_score = max(
        SECTION_MIN_PEAK_SCORE,
        float(column_scores.max()) * SECTION_BAND_MIN_SCORE_RATIO,
    )
    min_span = max(30, int(roi.shape[1] * SECTION_BAND_MIN_SEGMENT_RATIO))
    segments = find_dense_axis_segments(column_scores, min_score, min_span)
    if not segments:
        return None

    min_width = max(80, int(right_width * SECTION_BAND_MIN_WIDTH_RATIO))
    chosen_segment = None
    for start_idx, end_idx in segments:
        if end_idx - start_idx >= min_width:
            chosen_segment = (start_idx, end_idx)
            break

    if chosen_segment is None:
        chosen_segment = max(segments, key=lambda item: item[1] - item[0])

    best_start, best_end = chosen_segment
    segment_width = max(1, best_end - best_start)
    padded_start = max(
        0,
        best_start
        - max(
            SECTION_BAND_LEFT_PADDING_MIN,
            int(round(segment_width * SECTION_BAND_LEFT_PADDING_RATIO)),
        ),
    )
    padded_end = min(
        roi.shape[1],
        best_end
        + max(
            SECTION_BAND_RIGHT_PADDING_MIN,
            int(round(segment_width * SECTION_BAND_RIGHT_PADDING_RATIO)),
        ),
    )
    return (
        search_x1 + padded_start,
        search_y1,
        search_x1 + padded_end,
        search_y2,
    )


def find_section_projection_peaks(gray, rx2, center_full=None, outer_r=None):
    """SECTION band 내부의 주요 수직/수평 치수선 위치를 peak로 뽑는다."""
    section_bounds = find_section_content_band(gray, rx2, center_full, outer_r)
    if section_bounds is None:
        return [], [], None

    section_x1, section_y1, section_x2, section_y2 = section_bounds
    roi = gray[section_y1:section_y2, section_x1:section_x2]
    if roi.size == 0:
        return [], [], None

    _, binary = cv2.threshold(
        roi,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    horizontal_kernel_w = max(25, int(roi.shape[1] * SECTION_HORIZONTAL_KERNEL_RATIO))
    vertical_kernel_h = max(25, int(roi.shape[0] * SECTION_VERTICAL_KERNEL_RATIO))
    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (horizontal_kernel_w, 1),
    )
    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, vertical_kernel_h),
    )
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
        roi.shape[1] * SECTION_MIN_ROW_SCORE_RATIO,
        float(row_scores.max()) * SECTION_MIN_ROW_RELATIVE_RATIO,
    )
    col_min_score = max(
        SECTION_MIN_PEAK_SCORE,
        roi.shape[0] * SECTION_MIN_COL_SCORE_RATIO,
        float(col_scores.max()) * SECTION_MIN_COL_RELATIVE_RATIO,
    )
    row_peak_distance = max(20, int(roi.shape[0] * SECTION_ROW_PEAK_DISTANCE_RATIO))
    col_peak_distance = max(20, int(roi.shape[1] * SECTION_COL_PEAK_DISTANCE_RATIO))

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

    edge_window = max(40, int(roi.shape[1] * SECTION_EDGE_WINDOW_RATIO))
    edge_min_score = max(col_min_score, float(col_scores.max()) * SECTION_EDGE_PEAK_MIN_SCORE_RATIO)
    edge_candidates: list[int] = []
    for window_start, window_end in [
        (0, min(edge_window, roi.shape[1])),
        (max(0, roi.shape[1] - edge_window), roi.shape[1]),
    ]:
        if window_end <= window_start:
            continue
        local_scores = col_scores[window_start:window_end].copy()
        if local_scores.size == 0:
            continue
        for existing_idx in col_indices:
            if not (window_start <= existing_idx < window_end):
                continue
            mask_start = max(0, existing_idx - window_start - SECTION_EDGE_PEAK_MIN_SEPARATION)
            mask_end = min(
                local_scores.size,
                existing_idx - window_start + SECTION_EDGE_PEAK_MIN_SEPARATION + 1,
            )
            local_scores[mask_start:mask_end] = 0.0
        local_idx = int(np.argmax(local_scores)) + window_start
        if float(col_scores[local_idx]) < edge_min_score:
            continue
        if any(abs(local_idx - existing_idx) < SECTION_EDGE_PEAK_MIN_SEPARATION for existing_idx in col_indices):
            continue
        if any(abs(local_idx - existing_idx) < SECTION_EDGE_PEAK_MIN_SEPARATION for existing_idx in edge_candidates):
            continue
        edge_candidates.append(local_idx)

    if edge_candidates:
        col_indices = sorted(
            col_indices + edge_candidates[:SECTION_EDGE_EXTRA_VERTICAL_LINES],
            key=lambda idx: float(col_scores[idx]),
            reverse=True,
        )
        col_indices = sorted(col_indices)

    top_edge_window = max(40, int(roi.shape[0] * SECTION_TOP_EDGE_WINDOW_RATIO))
    top_edge_min_score = max(
        SECTION_MIN_PEAK_SCORE,
        float(row_scores.max()) * SECTION_TOP_EDGE_MIN_SCORE_RATIO,
    )
    top_edge_candidates: list[int] = []
    local_top_scores = row_scores[:top_edge_window].copy()
    for existing_idx in row_indices:
        if existing_idx >= top_edge_window:
            continue
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

    section_width = max(1, section_x2 - section_x1)
    full_search_x2 = max(section_x2 + 1, gray.shape[1] - max(20, int(gray.shape[1] * 0.02)))
    outer_search_x1 = section_x2
    outer_search_x2 = min(
        full_search_x2,
        section_x2 + max(120, int(section_width * SECTION_OUTER_SEARCH_RATIO)),
    )
    if outer_search_x2 > outer_search_x1:
        outer_roi = gray[section_y1:section_y2, outer_search_x1:outer_search_x2]
        if outer_roi.size > 0:
            _, outer_binary = cv2.threshold(
                outer_roi,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
            )
            outer_vertical = cv2.morphologyEx(outer_binary, cv2.MORPH_OPEN, vertical_kernel)
            outer_col_scores = smooth_signal(
                outer_vertical.sum(axis=0).astype(np.float32) / 255.0,
                SECTION_SMOOTH_WINDOW,
            )
            outer_min_score = max(
                SECTION_MIN_PEAK_SCORE,
                float(outer_col_scores.max()) * SECTION_OUTER_PEAK_MIN_SCORE_RATIO,
            )
            outer_peak_distance = max(
                20,
                int(section_width * SECTION_OUTER_PEAK_DISTANCE_RATIO),
            )
            outer_indices = select_peak_indices(
                outer_col_scores,
                outer_min_score,
                outer_peak_distance,
                SECTION_OUTER_MAX_VERTICAL_LINES,
            )
            for outer_idx in outer_indices:
                global_x = outer_search_x1 + outer_idx
                if any(abs(global_x - existing_x) < SECTION_EDGE_PEAK_MIN_SEPARATION for existing_x in vertical_cols):
                    continue
                vertical_cols.append(global_x)
            vertical_cols.sort()

    return vertical_cols, horizontal_rows, section_bounds


def collect_projection_data(gray):
    """전체 도면에서 직선 투사에 필요한 끝점 좌표를 수집한다."""
    rx1, ry1, rx2, ry2 = find_main_view_region(gray)
    roi_gray = gray[ry1:ry2, rx1:rx2]
    roi_h, roi_w = roi_gray.shape
    min_r = int(min(roi_h, roi_w) * MIN_R_RATIO)
    max_r = int(min(roi_h, roi_w) * MAX_R_RATIO)

    raw_circles_roi = detect_concentric_alt(roi_gray, min_r, max_r)
    circles_roi = select_primary_concentric_circles(raw_circles_roi)
    circles_full = [(cx + rx1, cy + ry1, r) for cx, cy, r in circles_roi]

    peaks_full = []
    outer_r = None
    center_full = None
    auxiliary_rows = []
    auxiliary_bounds = None
    section_vertical_cols = []
    section_horizontal_rows = []
    section_bounds = None
    if circles_roi:
        outer_r = max(c[2] for c in circles_roi)
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
            rx2,
            center_full,
            outer_r,
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
    }


def build_circle_lines(circles_full):
    dir_colors = {
        "N": (255, 100, 100),
        "S": (255, 100, 100),
        "E": (0, 200, 255),
        "W": (0, 200, 255),
    }
    lines = []
    for cx, cy, r in circles_full:
        for dir_name, ddx, ddy, axis in [
            ("N", 0, -1, "h"),
            ("S", 0, 1, "h"),
            ("E", 1, 0, "v"),
            ("W", -1, 0, "v"),
        ]:
            px = int(round(cx + r * ddx))
            py = int(round(cy + r * ddy))
            lines.append(
                {
                    "px": px,
                    "py": py,
                    "axis": axis,
                    "color": dir_colors[dir_name],
                    "dir_name": dir_name,
                    "cx": float(cx),
                    "cy": float(cy),
                    "r": float(r),
                }
            )
    return lines


def attach_circle_hits(circle_lines, arrows=None, hit_tolerance=15):
    arrows = arrows or []
    annotated = []
    for line in circle_lines:
        hits = []
        cx = line["cx"]
        cy = line["cy"]
        r = line["r"]
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - line["py"]) <= hit_tolerance:
                if np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2) < r * 0.9:
                    continue
                hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - line["px"]) <= hit_tolerance:
                if np.sqrt((ax - cx) ** 2 + (ay - cy) ** 2) < r * 0.9:
                    continue
                hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def build_protrusion_lines(peaks_full, center_full, outer_r):
    lines = []
    if not peaks_full or center_full is None or outer_r is None:
        return lines

    ccx, ccy = center_full
    for angle, _, ppx, ppy in peaks_full:
        for axis in ["h", "v"]:
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
    auxiliary_rows,
    center_full,
    section_vertical_cols=None,
    section_horizontal_rows=None,
    section_bounds=None,
):
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


def attach_protrusion_hits(protrusion_lines, arrows=None, hit_tolerance=15):
    arrows = arrows or []
    annotated = []
    for line in protrusion_lines:
        hits = []
        ccx = line["ccx"]
        ccy = line["ccy"]
        outer_r = line["outer_r"]
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - line["py"]) <= hit_tolerance:
                if np.sqrt((ax - ccx) ** 2 + (ay - ccy) ** 2) > outer_r * 0.9:
                    hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - line["px"]) <= hit_tolerance:
                if np.sqrt((ax - ccx) ** 2 + (ay - ccy) ** 2) > outer_r * 0.9:
                    hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def attach_auxiliary_hits(auxiliary_lines, arrows=None, hit_tolerance=15):
    arrows = arrows or []
    annotated = []
    for line in auxiliary_lines:
        hits = []
        for arrow in arrows:
            ax, ay = arrow["x"], arrow["y"]
            if line["axis"] == "h" and abs(ay - line["py"]) <= hit_tolerance:
                hits.append((int(ax), int(ay)))
            elif line["axis"] == "v" and abs(ax - line["px"]) <= hit_tolerance:
                hits.append((int(ax), int(ay)))
        annotated.append({**line, "hits": hits})
    return annotated


def draw_projection_axis(canvas, line, full_w, full_h, thickness):
    if line["axis"] == "h":
        cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), line["color"], thickness)
    else:
        cv2.line(canvas, (line["px"], 0), (line["px"], full_h), line["color"], thickness)


def draw_fullpage_projection(
    img,
    circles_full,
    circle_lines,
    protrusion_lines,
    gt,
    name,
    auxiliary_lines=None,
):
    full_h, full_w = img.shape[:2]
    canvas = img.copy()
    auxiliary_lines = auxiliary_lines or []

    for cx, cy, r in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 3)

    circle_hit = 0
    circle_hit_lines = 0
    for line in circle_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        cv2.circle(
            canvas,
            (line["px"], line["py"]),
            8,
            (255, 255, 255),
            2 if line["hits"] else 1,
        )
        if not line["hits"]:
            continue
        circle_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (0, 0, 255),
                cv2.MARKER_TILTED_CROSS,
                15,
                2,
            )
            circle_hit += 1

    protrusion_hit = 0
    protrusion_hit_lines = 0
    for line in protrusion_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        cv2.drawMarker(
            canvas,
            (line["px"], line["py"]),
            (0, 0, 255),
            cv2.MARKER_DIAMOND,
            12,
            3 if line["hits"] else 1,
        )
        if not line["hits"]:
            continue
        protrusion_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (255, 0, 200),
                cv2.MARKER_TILTED_CROSS,
                12,
                2,
            )
            protrusion_hit += 1

    auxiliary_hit = 0
    auxiliary_hit_lines = 0
    section_hit = 0
    section_hit_lines = 0
    for line in auxiliary_lines:
        draw_projection_axis(canvas, line, full_w, full_h, 2 if line["hits"] else 1)
        if not line["hits"]:
            continue
        if line.get("source") == "section":
            section_hit_lines += 1
        else:
            auxiliary_hit_lines += 1
        for hx, hy in line["hits"]:
            cv2.drawMarker(
                canvas,
                (hx, hy),
                (0, 165, 255) if line.get("source") != "section" else (0, 215, 255),
                cv2.MARKER_TILTED_CROSS,
                12,
                2,
            )
            if line.get("source") == "section":
                section_hit += 1
            else:
                auxiliary_hit += 1

    total_lines = len(circle_lines) + len(protrusion_lines) + len(auxiliary_lines)
    active_lines = (
        circle_hit_lines
        + protrusion_hit_lines
        + auxiliary_hit_lines
        + section_hit_lines
    )
    print(f"  전체 직선: {total_lines}개 → 히트 있는 직선: {active_lines}개")
    print(f"  동심원 히트: {circle_hit}개 ({circle_hit_lines}개 직선)")
    print(f"  돌출부 히트: {protrusion_hit}개 ({protrusion_hit_lines}개 직선)")
    if auxiliary_lines:
        print(f"  보조도 히트: {auxiliary_hit}개 ({auxiliary_hit_lines}개 직선)")
        print(f"  SECTION 히트: {section_hit}개 ({section_hit_lines}개 직선)")

    auxiliary_count = sum(1 for line in auxiliary_lines if line.get("source") == "auxiliary")
    section_count = sum(1 for line in auxiliary_lines if line.get("source") == "section")

    for cx, cy, r in circles_full:
        cv2.putText(
            canvas,
            f"r={r:.0f}",
            (int(cx + r * 0.7), int(cy - r * 0.3)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (67, 160, 71),
            2,
        )

    pil = add_header(
        canvas,
        f"{name.upper()} — Cardinal v3 + Protrusion ({full_w}x{full_h})",
        f"동심원 {len(circles_full)}개 + 돌출 {len(protrusion_lines) // 2}개 + "
        f"보조도 {auxiliary_count}개 + SECTION {section_count}개 | "
        f"히트: 원{circle_hit} + 돌출{protrusion_hit} + 보조{auxiliary_hit} + SECTION{section_hit}",
        f"GT: OD={gt['od']} ID={gt['id']}",
    )
    return pil


def draw_projection_lines_only(
    img,
    circles_full,
    circle_lines,
    peaks_full,
    protrusion_lines,
    auxiliary_lines=None,
):
    """문서용: 끝점과 직선만 남긴 깔끔한 투사선 시각화."""
    full_h, full_w = img.shape[:2]
    canvas = img.copy()
    auxiliary_lines = auxiliary_lines or []

    for cx, cy, r in circles_full:
        cv2.circle(canvas, (int(cx), int(cy)), int(r), (67, 160, 71), 4)

    circle_endpoint_color = (255, 255, 0)
    horizontal_color = (255, 255, 0)
    vertical_color = (0, 255, 255)
    protrusion_color = (255, 0, 200)

    for line in circle_lines:
        color = horizontal_color if line["axis"] == "h" else vertical_color
        if line["axis"] == "h":
            cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), color, 2)
        else:
            cv2.line(canvas, (line["px"], 0), (line["px"], full_h), color, 2)
        cv2.circle(canvas, (line["px"], line["py"]), 10, circle_endpoint_color, -1)
        cv2.circle(canvas, (line["px"], line["py"]), 14, (60, 60, 60), 2)

    for line in protrusion_lines:
        if line["axis"] == "h":
            cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), protrusion_color, 2)
        else:
            cv2.line(canvas, (line["px"], 0), (line["px"], full_h), protrusion_color, 2)

    for line in auxiliary_lines:
        color = line.get("color", horizontal_color if line["axis"] == "h" else vertical_color)
        if line["axis"] == "h":
            cv2.line(canvas, (0, line["py"]), (full_w, line["py"]), color, 2)
        else:
            cv2.line(canvas, (line["px"], 0), (line["px"], full_h), color, 2)

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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[gt["name"] for gt in GT.values()],
        help="특정 도면만 처리",
    )
    parser.add_argument(
        "--lines-only",
        action="store_true",
        help="화살촉 히트 없이 끝점과 투사선만 그린 이미지 생성",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    print("S08 Cardinal v3 — 전체 도면 투사 + 4방향 돌출부")
    print("=" * 60)

    targets = [
        (doc_id, gt)
        for doc_id, gt in GT.items()
        if args.doc is None or gt["name"] == args.doc
    ]

    for doc_id, gt in targets:
        name = gt["name"]
        img_path = SRC_DIR / f"{doc_id}.png"
        if not img_path.exists():
            print(f"⚠ {name}: {img_path} 없음")
            continue

        print(f"\n{name.upper()} — {doc_id} (GT: OD={gt['od']} ID={gt['id']})")

        img = cv2.imread(str(img_path))
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        full_h, full_w = gray.shape
        print(f"  전체 도면: {full_w}x{full_h}")

        data = collect_projection_data(gray)
        circles_full = data["circles_full"]
        peaks_full = data["peaks_full"]
        outer_r = data["outer_r"]
        center_full = data["center_full"]
        auxiliary_rows = data["auxiliary_rows"]
        section_vertical_cols = data["section_vertical_cols"]
        section_horizontal_rows = data["section_horizontal_rows"]

        print(
            f"  ALT 후보: {len(data['raw_circles_roi'])}개 → "
            f"주 동심원: {len(circles_full)}개"
        )
        print(f"  돌출 끝점: {len(peaks_full)}개")
        print(f"  보조도 수평선: {len(auxiliary_rows)}개 ({auxiliary_rows})")
        print(
            f"  SECTION 수직선: {len(section_vertical_cols)}개 "
            f"({section_vertical_cols})"
        )
        print(
            f"  SECTION 수평선: {len(section_horizontal_rows)}개 "
            f"({section_horizontal_rows})"
        )

        if not circles_full:
            continue

        # Shared geometry: lines-only/fullpage 모두 동일한 끝점 집합을 사용한다.
        base_circle_lines = build_circle_lines(circles_full)
        base_protrusion_lines = build_protrusion_lines(peaks_full, center_full, outer_r)
        auxiliary_lines = build_auxiliary_lines(
            auxiliary_rows,
            center_full,
            section_vertical_cols,
            section_horizontal_rows,
            data["section_bounds"],
        )

        if args.lines_only:
            print(
                f"  lines-only 산출물: 동심원 직선 {len(base_circle_lines)}개 + "
                f"돌출 직선 {len(base_protrusion_lines)}개 + "
                f"보조도 직선 {len(auxiliary_lines)}개"
            )
            pil = draw_projection_lines_only(
                img,
                circles_full,
                base_circle_lines,
                peaks_full,
                base_protrusion_lines,
                auxiliary_lines,
            )
            save_pil(pil, f"{name}_projection_lines_only.jpg", max_w=1600)
            continue

        arrows = detect_arrowheads(gray)
        print(f"  화살촉 후보: {len(arrows)}개")
        circle_lines = attach_circle_hits(base_circle_lines, arrows)
        protrusion_lines = attach_protrusion_hits(
            base_protrusion_lines,
            arrows,
        )
        auxiliary_hit_lines = attach_auxiliary_hits(auxiliary_lines, arrows)

        pil = draw_fullpage_projection(
            img,
            circles_full,
            circle_lines,
            protrusion_lines,
            gt,
            name,
            auxiliary_hit_lines,
        )
        save_pil(pil, f"{name}_cardinal_v3_full.jpg", max_w=1600)

    print(f"\n완료: {OUT_DIR}")


if __name__ == "__main__":
    run()
