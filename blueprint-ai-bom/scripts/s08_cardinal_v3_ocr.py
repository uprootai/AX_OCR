#!/usr/bin/env python3
"""S08 Cardinal Projection v3 - Hybrid pixel scan + line validation for 2-6/2-7."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests
from PIL import Image

from cardinal_common import (
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    save_pil,
)
from s08_cardinal_v3_endpoint_lines import (
    ENDPOINT_TOLERANCE,
    detect_lsd_segments,
    extract_endpoints,
    filter_endpoints_on_projections,
)
from s08_cardinal_v3_fullpage import (
    GT,
    SRC_DIR,
)
from s08_cardinal_v3_projection_endpoints import draw_projection_endpoint_overlay


def resolve_api_url(env_name: str, default_base_url: str, default_path: str) -> str:
    base_url = os.environ.get(env_name, default_base_url).rstrip("/")
    return base_url if base_url.endswith(default_path) else f"{base_url}{default_path}"


OCR_API = resolve_api_url("PADDLEOCR_API_URL", "http://localhost:5006", "/api/v1/ocr")
LINE_DETECTOR_API = resolve_api_url(
    "LINE_DETECTOR_API_URL",
    "http://localhost:5016",
    "/api/v1/process",
)

ENDPOINT_TOLERANCE = 20
OCR_SEARCH_RADIUS = 150.0
LINE_KEY_COORD_BIN = 10.0
LINE_KEY_SPAN_BIN = 20.0
FOCUS_REGION_PADDING = 80
AUXILIARY_FOCUS_PADDING = 120
SECTION_FOCUS_PADDING_X = 100
SECTION_FOCUS_PADDING_TOP = 120
SECTION_FOCUS_PADDING_BOTTOM = 320
OCR_SPAN_MARGIN = 90.0
OCR_PERPENDICULAR_TOLERANCE = 120.0
OCR_MIDPOINT_AXIS_WEIGHT = 0.35
OCR_PERPENDICULAR_WEIGHT = 1.6
OCR_SPAN_OUTSIDE_WEIGHT = 2.4
OCR_CONFIDENCE_BONUS = 20.0
PIXEL_SCAN_STRIP_HALF_WIDTH = 3
PIXEL_SCAN_DARK_THRESHOLD = 128
PIXEL_SCAN_DARK_RATIO_MIN = 0.15
LINE_DETECTOR_ALIGNMENT_TOLERANCE = 30.0
LINE_DETECTOR_OVERLAP_RATIO_MIN = 0.30
STRUCTURE_LINE_LENGTH_RATIO = 0.40
CONCENTRIC_CENTER_DISTANCE_RATIO = 0.30
EXCLUDED_VALIDATION_LINE_STYLES = {"dash_dot", "dashed"}
EXCLUDED_VALIDATION_SIGNAL_TYPES = {"centerline"}

HYBRID_CONFIRMED_COLOR = (0, 0, 255)
HYBRID_CONFIRMED_THICKNESS = 7
PIXEL_ONLY_COLOR = (0, 165, 255)
PIXEL_ONLY_THICKNESS = 2
OCR_BOX_COLOR = (255, 255, 255)
OCR_TEXT_COLOR = (40, 255, 40)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--doc",
        choices=[gt["name"] for gt in GT.values()],
        help="process one drawing only",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="skip OCR matching and render connected lines only",
    )
    return parser.parse_args()


def build_endpoint_match(endpoint: dict[str, float | int]) -> dict[str, Any]:
    return {
        "endpoint_idx": int(endpoint["endpoint_idx"]),
        "segment_idx": int(endpoint["segment_idx"]),
        "x": float(endpoint["x"]),
        "y": float(endpoint["y"]),
        "distance": 0.0,
    }


def get_line_waypoints(line: dict[str, Any]) -> list[tuple[float, float]]:
    raw_waypoints = line.get("waypoints")
    if isinstance(raw_waypoints, list):
        waypoints: list[tuple[float, float]] = []
        for point in raw_waypoints:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                waypoints.append((float(point[0]), float(point[1])))
            except (TypeError, ValueError):
                continue
        if len(waypoints) >= 2:
            return waypoints

    start = line.get("start_point", [0.0, 0.0])
    end = line.get("end_point", [0.0, 0.0])
    start_point = (float(start[0]), float(start[1]))
    end_point = (float(end[0]), float(end[1]))
    return [start_point, end_point]


def best_projection_index_for_endpoint(
    endpoint: dict[str, float | int],
    projection_lines: list[dict[str, Any]],
    axis: str,
) -> int | None:
    point_x = float(endpoint["x"])
    point_y = float(endpoint["y"])
    best_projection_idx: int | None = None
    best_delta = float("inf")

    for projection_idx, projection_line in enumerate(projection_lines):
        if projection_line["axis"] != axis:
            continue

        delta = (
            abs(point_y - float(projection_line["py"]))
            if axis == "h"
            else abs(point_x - float(projection_line["px"]))
        )
        if delta > ENDPOINT_TOLERANCE or delta >= best_delta:
            continue
        best_delta = delta
        best_projection_idx = projection_idx

    return best_projection_idx


def run_ocr(image_path: Path) -> list[dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            OCR_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("detections", [])


def run_line_detector(image_path: Path) -> list[dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            LINE_DETECTOR_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            data={
                "profile": "simple",
                "method": "lsd",
                "merge_lines": "true",
                "classify_types": "true",
                "classify_colors": "false",
                "classify_styles": "true",
                "find_intersections": "false",
                "detect_regions": "false",
                "visualize": "false",
                "include_svg": "false",
                "min_length": "0",
                "max_lines": "0",
            },
            timeout=120,
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("success") is False:
        raise RuntimeError(payload.get("error") or "Line Detector API request failed")

    result = payload.get("data", payload)
    lines = result.get("lines", [])
    return lines if isinstance(lines, list) else []


def parse_session_name_odid(ocr_detections: list[dict[str, Any]]) -> dict[str, Any]:
    """OCR 결과에서 세션명 텍스트를 찾아 OD/ID를 파싱한다.

    패턴: 'T1 BEARING ASSY (360X190)' → OD=360, ID=190
           'THRUST BEARING ASSY(OD670XID440)' → OD=670, ID=440
    """
    for det in ocr_detections:
        text = str(det.get("text", ""))
        if "ASSY" not in text.upper() and "BEARING" not in text.upper():
            continue
        m = re.search(r"(?:OD)?(\d+)\s*[Xx×]\s*(?:ID)?(\d+)", text)
        if m:
            od = int(m.group(1))
            id_val = int(m.group(2))
            return {"od": od, "id": id_val, "source_text": text}
    return {}


def build_projection_endpoint_candidates(
    gray: np.ndarray,
    projection_lines: list[dict[str, Any]],
) -> tuple[list[dict[str, float | int]], int]:
    lsd_segments = detect_lsd_segments(gray)
    endpoints = extract_endpoints(lsd_segments)
    filtered_endpoints = filter_endpoints_on_projections(
        endpoints,
        projection_lines,
        tolerance=ENDPOINT_TOLERANCE,
    )

    indexed_endpoints: list[dict[str, float | int]] = []
    for endpoint_idx, endpoint in enumerate(filtered_endpoints):
        indexed_endpoints.append(
            {
                **endpoint,
                "endpoint_idx": endpoint_idx,
            }
        )
    return indexed_endpoints, len(lsd_segments)


def dedupe_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for line in sorted(
        lines,
        key=lambda item: (
            float(item.get("priority_score", item.get("length", 0.0))),
            float(item.get("length", 0.0)),
        ),
        reverse=True,
    ):
        start_point = line["start_point_xy"]
        end_point = line["end_point_xy"]
        alignment = line["projection_alignment"]
        axis = alignment["axis"]

        if axis == "h":
            coord = round(((start_point[1] + end_point[1]) / 2.0) / LINE_KEY_COORD_BIN)
            span_start = round(min(start_point[0], end_point[0]) / LINE_KEY_SPAN_BIN)
            span_end = round(max(start_point[0], end_point[0]) / LINE_KEY_SPAN_BIN)
        else:
            coord = round(((start_point[0] + end_point[0]) / 2.0) / LINE_KEY_COORD_BIN)
            span_start = round(min(start_point[1], end_point[1]) / LINE_KEY_SPAN_BIN)
            span_end = round(max(start_point[1], end_point[1]) / LINE_KEY_SPAN_BIN)

        key = (
            axis,
            coord,
            span_start,
            span_end,
            tuple(alignment["projection_indices"][:2]),
        )
        if key in deduped:
            continue
        deduped[key] = line

    return list(deduped.values())


def clamp_rect(
    rect: tuple[int, int, int, int],
    image_shape: tuple[int, int],
    padding: int = 0,
) -> tuple[int, int, int, int] | None:
    return expand_rect(rect, image_shape, (padding, padding, padding, padding))


def expand_rect(
    rect: tuple[int, int, int, int],
    image_shape: tuple[int, int],
    padding: tuple[int, int, int, int],
) -> tuple[int, int, int, int] | None:
    height, width = image_shape
    x1, y1, x2, y2 = rect
    pad_left, pad_top, pad_right, pad_bottom = padding
    x1 = max(0, x1 - pad_left)
    y1 = max(0, y1 - pad_top)
    x2 = min(width, x2 + pad_right)
    y2 = min(height, y2 + pad_bottom)
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)


def build_focus_regions(
    image_shape: tuple[int, int],
    main_view_region: tuple[int, int, int, int],
    auxiliary_bounds: tuple[int, int, int, int] | None,
    section_bounds: tuple[int, int, int, int] | None,
    section_vertical_cols: list[int] | None = None,
) -> list[tuple[int, int, int, int]]:
    regions: list[tuple[int, int, int, int]] = []
    main_expanded = clamp_rect(main_view_region, image_shape, padding=FOCUS_REGION_PADDING)
    if main_expanded is not None:
        regions.append(main_expanded)
    if auxiliary_bounds is not None:
        auxiliary_expanded = clamp_rect(
            auxiliary_bounds,
            image_shape,
            padding=AUXILIARY_FOCUS_PADDING,
        )
        if auxiliary_expanded is not None:
            regions.append(auxiliary_expanded)
    if section_bounds is not None:
        section_vertical_cols = section_vertical_cols or []
        extra_left = max(
            SECTION_FOCUS_PADDING_X,
            section_bounds[0] - min(section_vertical_cols) + SECTION_FOCUS_PADDING_X
            if section_vertical_cols and min(section_vertical_cols) < section_bounds[0]
            else SECTION_FOCUS_PADDING_X,
        )
        extra_right = max(
            SECTION_FOCUS_PADDING_X,
            max(section_vertical_cols) - section_bounds[2] + SECTION_FOCUS_PADDING_X
            if section_vertical_cols and max(section_vertical_cols) > section_bounds[2]
            else SECTION_FOCUS_PADDING_X,
        )
        section_expanded = expand_rect(
            section_bounds,
            image_shape,
            (
                extra_left,
                SECTION_FOCUS_PADDING_TOP,
                extra_right,
                SECTION_FOCUS_PADDING_BOTTOM,
            ),
        )
        if section_expanded is not None:
            regions.append(section_expanded)
    return regions


def point_in_rect(point: tuple[float, float], rect: tuple[int, int, int, int]) -> bool:
    x, y = point
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def line_in_focus_regions(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    axis: str,
    focus_regions: list[tuple[int, int, int, int]],
) -> bool:
    midpoint = (
        (start_point[0] + end_point[0]) / 2.0,
        (start_point[1] + end_point[1]) / 2.0,
    )
    for rect in focus_regions:
        if point_in_rect(start_point, rect) or point_in_rect(end_point, rect) or point_in_rect(midpoint, rect):
            return True

        x1, y1, x2, y2 = rect
        if axis == "h":
            if y1 <= midpoint[1] <= y2 and max(start_point[0], end_point[0]) >= x1 and min(start_point[0], end_point[0]) <= x2:
                return True
            continue

        if x1 <= midpoint[0] <= x2 and max(start_point[1], end_point[1]) >= y1 and min(start_point[1], end_point[1]) <= y2:
            return True

    return False


def filter_lines_to_focus_regions(
    lines: list[dict[str, Any]],
    focus_regions: list[tuple[int, int, int, int]],
) -> list[dict[str, Any]]:
    if not focus_regions:
        return lines

    filtered: list[dict[str, Any]] = []
    for line in lines:
        start_point = line["start_point_xy"]
        end_point = line["end_point_xy"]
        axis = line["projection_alignment"]["axis"]
        if line_in_focus_regions(start_point, end_point, axis, focus_regions):
            filtered.append(line)
    return filtered


def group_projection_endpoints(
    projection_endpoints: list[dict[str, float | int]],
    projection_lines: list[dict[str, Any]],
) -> dict[tuple[str, int], list[dict[str, float | int]]]:
    grouped: dict[tuple[str, int], list[dict[str, float | int]]] = {}

    for endpoint in projection_endpoints:
        for axis in ("h", "v"):
            projection_idx = best_projection_index_for_endpoint(
                endpoint,
                projection_lines,
                axis,
            )
            if projection_idx is None:
                continue
            grouped.setdefault((axis, projection_idx), []).append(endpoint)

    return grouped


def scan_strip_dark_ratio(
    gray: np.ndarray,
    axis: str,
    start_coord: float,
    end_coord: float,
    fixed_coord: float,
) -> float:
    height, width = gray.shape[:2]

    if axis == "h":
        y_center = int(round(fixed_coord))
        x1 = max(0, int(round(min(start_coord, end_coord))))
        x2 = min(width - 1, int(round(max(start_coord, end_coord))))
        y1 = max(0, y_center - PIXEL_SCAN_STRIP_HALF_WIDTH)
        y2 = min(height - 1, y_center + PIXEL_SCAN_STRIP_HALF_WIDTH)
        if x2 <= x1 or y2 < y1:
            return 0.0

        strip = gray[y1 : y2 + 1, x1 : x2 + 1]
        # 각 x열에서 최소 밝기 = 가장 어두운 픽셀 (선이 1px이라도 있으면 잡힘)
        min_profile = np.min(strip, axis=0)
    else:
        x_center = int(round(fixed_coord))
        y1 = max(0, int(round(min(start_coord, end_coord))))
        y2 = min(height - 1, int(round(max(start_coord, end_coord))))
        x1 = max(0, x_center - PIXEL_SCAN_STRIP_HALF_WIDTH)
        x2 = min(width - 1, x_center + PIXEL_SCAN_STRIP_HALF_WIDTH)
        if y2 <= y1 or x2 < x1:
            return 0.0

        strip = gray[y1 : y2 + 1, x1 : x2 + 1]
        # 각 y행에서 최소 밝기
        min_profile = np.min(strip, axis=1)

    if min_profile.size == 0:
        return 0.0
    return float(np.mean(min_profile < PIXEL_SCAN_DARK_THRESHOLD))


def build_pixel_connection(
    start_endpoint: dict[str, float | int],
    end_endpoint: dict[str, float | int],
    projection_line: dict[str, Any],
    projection_idx: int,
    dark_ratio: float,
) -> dict[str, Any]:
    axis = str(projection_line["axis"])

    if axis == "h":
        fixed_coord = float(projection_line["py"])
        ordered = sorted(
            (start_endpoint, end_endpoint),
            key=lambda endpoint: (float(endpoint["x"]), float(endpoint["y"])),
        )
        start_point = (float(ordered[0]["x"]), fixed_coord)
        end_point = (float(ordered[1]["x"]), fixed_coord)
        length = abs(end_point[0] - start_point[0])
        angle = 0.0
    else:
        fixed_coord = float(projection_line["px"])
        ordered = sorted(
            (start_endpoint, end_endpoint),
            key=lambda endpoint: (float(endpoint["y"]), float(endpoint["x"])),
        )
        start_point = (fixed_coord, float(ordered[0]["y"]))
        end_point = (fixed_coord, float(ordered[1]["y"]))
        length = abs(end_point[1] - start_point[1])
        angle = 90.0

    ordered_start_endpoint, ordered_end_endpoint = ordered
    midpoint = (
        (start_point[0] + end_point[0]) / 2.0,
        (start_point[1] + end_point[1]) / 2.0,
    )
    return {
        "id": (
            f"pixel-scan-{axis}-{projection_idx}-"
            f"{int(ordered_start_endpoint['endpoint_idx'])}-"
            f"{int(ordered_end_endpoint['endpoint_idx'])}"
        ),
        "start_point": start_point,
        "end_point": end_point,
        "waypoints": [list(start_point), list(end_point)],
        "length": float(length),
        "angle": angle,
        "pixel_scan_dark_ratio": dark_ratio,
        "priority_score": dark_ratio * 1000.0 + float(length),
        "scan_method": "pixel_strip",
        "start_match": build_endpoint_match(ordered_start_endpoint),
        "end_match": build_endpoint_match(ordered_end_endpoint),
        "projection_alignment": {
            "axis": axis,
            "projection_indices": [projection_idx],
        },
        "start_point_xy": start_point,
        "end_point_xy": end_point,
        "midpoint": midpoint,
    }


def build_pair_coordinate_key(line: dict[str, Any]) -> tuple[float, float, float, float]:
    start_x, start_y = line["start_point_xy"]
    end_x, end_y = line["end_point_xy"]
    return (
        round(float(start_x), 3),
        round(float(start_y), 3),
        round(float(end_x), 3),
        round(float(end_y), 3),
    )


def scan_pixel_connections(
    gray: np.ndarray,
    projection_endpoints: list[dict[str, float | int]],
    projection_lines: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pair_lines: list[dict[str, Any]] = []
    seen_pair_coords: set[tuple[float, float, float, float]] = set()
    grouped_endpoints = group_projection_endpoints(
        projection_endpoints,
        projection_lines,
    )

    for (axis, projection_idx), endpoints in grouped_endpoints.items():
        if len(endpoints) < 2:
            continue

        ordered_endpoints = sorted(
            endpoints,
            key=(
                (lambda endpoint: (float(endpoint["x"]), float(endpoint["y"])))
                if axis == "h"
                else (lambda endpoint: (float(endpoint["y"]), float(endpoint["x"])))
            ),
        )
        fixed_coord = (
            float(projection_lines[projection_idx]["py"])
            if axis == "h"
            else float(projection_lines[projection_idx]["px"])
        )

        for i in range(len(ordered_endpoints)):
            for j in range(i + 1, min(i + 3, len(ordered_endpoints))):
                start_endpoint = ordered_endpoints[i]
                end_endpoint = ordered_endpoints[j]
                start_coord = (
                    float(start_endpoint["x"])
                    if axis == "h"
                    else float(start_endpoint["y"])
                )
                end_coord = (
                    float(end_endpoint["x"])
                    if axis == "h"
                    else float(end_endpoint["y"])
                )
                if abs(end_coord - start_coord) < 2.0:
                    continue

                dark_ratio = scan_strip_dark_ratio(
                    gray,
                    axis,
                    start_coord,
                    end_coord,
                    fixed_coord,
                )
                if dark_ratio < PIXEL_SCAN_DARK_RATIO_MIN:
                    continue

                pair_line = build_pixel_connection(
                    start_endpoint,
                    end_endpoint,
                    projection_lines[projection_idx],
                    projection_idx,
                    dark_ratio,
                )
                pair_key = build_pair_coordinate_key(pair_line)
                if pair_key in seen_pair_coords:
                    continue
                seen_pair_coords.add(pair_key)
                pair_lines.append(pair_line)

    pair_lines = dedupe_lines(pair_lines)
    return list(pair_lines), pair_lines


def iter_line_waypoint_segments(
    line: dict[str, Any],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    waypoints = get_line_waypoints(line)
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for start_point, end_point in zip(waypoints, waypoints[1:]):
        if start_point == end_point:
            continue
        segments.append((start_point, end_point))
    return segments


def build_line_detector_spans(
    line_detector_lines: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    spans: dict[str, list[dict[str, Any]]] = {"h": [], "v": []}

    for fallback_idx, line in enumerate(line_detector_lines):
        line_id = str(line.get("id", fallback_idx))
        for start_point, end_point in iter_line_waypoint_segments(line):
            x1, y1 = start_point
            x2, y2 = end_point
            if (
                abs(x2 - x1) >= 1.0
                and abs(y2 - y1) <= LINE_DETECTOR_ALIGNMENT_TOLERANCE
            ):
                spans["h"].append(
                    {
                        "line_id": line_id,
                        "coord": (y1 + y2) / 2.0,
                        "start": min(x1, x2),
                        "end": max(x1, x2),
                    }
                )
            if (
                abs(y2 - y1) >= 1.0
                and abs(x2 - x1) <= LINE_DETECTOR_ALIGNMENT_TOLERANCE
            ):
                spans["v"].append(
                    {
                        "line_id": line_id,
                        "coord": (x1 + x2) / 2.0,
                        "start": min(y1, y2),
                        "end": max(y1, y2),
                    }
                )

    return spans


def normalize_line_detector_label(value: Any) -> str:
    return str(value or "").strip().lower()


def blocked_line_detector_reasons(line: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    line_style = normalize_line_detector_label(line.get("line_style"))
    signal_type = normalize_line_detector_label(line.get("signal_type"))
    if line_style in EXCLUDED_VALIDATION_LINE_STYLES:
        reasons.append(f"line_style:{line_style}")
    if signal_type in EXCLUDED_VALIDATION_SIGNAL_TYPES:
        reasons.append(f"signal_type:{signal_type}")
    return reasons


def split_line_detector_lines(
    line_detector_lines: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_lines: list[dict[str, Any]] = []
    blocked_lines: list[dict[str, Any]] = []

    for line in line_detector_lines:
        reasons = blocked_line_detector_reasons(line)
        if reasons:
            blocked_lines.append({**line, "_blocked_reasons": reasons})
            continue
        allowed_lines.append(line)

    return allowed_lines, blocked_lines


def merge_spans(
    spans: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if not spans:
        return []

    ordered_spans = sorted(spans, key=lambda span: (span[0], span[1]))
    merged: list[list[float]] = [[ordered_spans[0][0], ordered_spans[0][1]]]
    for start, end in ordered_spans[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
            continue
        merged.append([start, end])
    return [(start, end) for start, end in merged]


def compute_line_detector_overlap(
    pair_line: dict[str, Any],
    line_detector_spans: dict[str, list[dict[str, Any]]],
) -> tuple[float, list[str]]:
    axis = str(pair_line["projection_alignment"]["axis"])
    start_point = pair_line["start_point_xy"]
    end_point = pair_line["end_point_xy"]
    if axis == "h":
        fixed_coord = float(pair_line["midpoint"][1])
        pair_start = min(float(start_point[0]), float(end_point[0]))
        pair_end = max(float(start_point[0]), float(end_point[0]))
    else:
        fixed_coord = float(pair_line["midpoint"][0])
        pair_start = min(float(start_point[1]), float(end_point[1]))
        pair_end = max(float(start_point[1]), float(end_point[1]))

    pair_length = max(pair_end - pair_start, 1.0)
    overlap_spans: list[tuple[float, float]] = []
    supporting_line_ids: set[str] = set()
    for line_span in line_detector_spans[axis]:
        if abs(float(line_span["coord"]) - fixed_coord) > LINE_DETECTOR_ALIGNMENT_TOLERANCE:
            continue

        overlap_start = max(pair_start, float(line_span["start"]))
        overlap_end = min(pair_end, float(line_span["end"]))
        if overlap_end <= overlap_start:
            continue

        overlap_spans.append((overlap_start, overlap_end))
        supporting_line_ids.add(str(line_span["line_id"]))

    merged_overlap_spans = merge_spans(overlap_spans)
    overlap_length = sum(end - start for start, end in merged_overlap_spans)
    return overlap_length / pair_length, sorted(supporting_line_ids)


def exceeds_structure_length_limit(
    pair_line: dict[str, Any],
    image_shape: tuple[int, int] | tuple[int, int, int],
) -> bool:
    height, width = image_shape[:2]
    axis = str(pair_line["projection_alignment"]["axis"])
    length_limit = (width if axis == "h" else height) * STRUCTURE_LINE_LENGTH_RATIO
    return float(pair_line.get("length", 0.0)) >= length_limit


def crosses_concentric_centerline(
    pair_line: dict[str, Any],
    center_full: tuple[float, float] | None,
    outer_r: float | None,
) -> bool:
    if center_full is None or outer_r is None or outer_r <= 0:
        return False

    center_x = float(center_full[0])
    center_y = float(center_full[1])
    axis = str(pair_line["projection_alignment"]["axis"])
    start_point = pair_line["start_point_xy"]
    end_point = pair_line["end_point_xy"]

    if axis == "h":
        span_start = min(float(start_point[0]), float(end_point[0]))
        span_end = max(float(start_point[0]), float(end_point[0]))
        if not span_start <= center_x <= span_end:
            return False
        perpendicular_distance = abs(float(pair_line["midpoint"][1]) - center_y)
    else:
        span_start = min(float(start_point[1]), float(end_point[1]))
        span_end = max(float(start_point[1]), float(end_point[1]))
        if not span_start <= center_y <= span_end:
            return False
        perpendicular_distance = abs(float(pair_line["midpoint"][0]) - center_x)

    return perpendicular_distance < float(outer_r) * CONCENTRIC_CENTER_DISTANCE_RATIO


def validate_pixel_connections_with_line_detector(
    pixel_candidate_lines: list[dict[str, Any]],
    line_detector_lines: list[dict[str, Any]],
    image_shape: tuple[int, int] | tuple[int, int, int],
    center_full: tuple[float, float] | None = None,
    outer_r: float | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_detector_lines, blocked_detector_lines = split_line_detector_lines(line_detector_lines)
    line_detector_spans = build_line_detector_spans(allowed_detector_lines)
    blocked_detector_spans = build_line_detector_spans(blocked_detector_lines)
    confirmed_lines: list[dict[str, Any]] = []
    pixel_only_lines: list[dict[str, Any]] = []
    filtered_out_lines: list[dict[str, Any]] = []

    for candidate_line in pixel_candidate_lines:
        blocked_overlap_ratio, blocked_supporting_ids = compute_line_detector_overlap(
            candidate_line,
            blocked_detector_spans,
        )
        filter_reasons: list[str] = []
        if blocked_overlap_ratio >= LINE_DETECTOR_OVERLAP_RATIO_MIN:
            filter_reasons.append("line_detector_blocked_style")
        if exceeds_structure_length_limit(candidate_line, image_shape):
            filter_reasons.append("structure_length")
        if crosses_concentric_centerline(candidate_line, center_full, outer_r):
            filter_reasons.append("concentric_centerline")
        if filter_reasons:
            filtered_out_lines.append(
                {
                    **candidate_line,
                    "filter_reasons": filter_reasons,
                    "blocked_overlap_ratio": blocked_overlap_ratio,
                    "blocked_supporting_ids": blocked_supporting_ids,
                }
            )
            continue

        overlap_ratio, supporting_line_ids = compute_line_detector_overlap(
            candidate_line,
            line_detector_spans,
        )
        enriched_line = {
            **candidate_line,
            "line_detector_overlap_ratio": overlap_ratio,
            "line_detector_supporting_ids": supporting_line_ids,
            "blocked_overlap_ratio": blocked_overlap_ratio,
            "blocked_supporting_ids": blocked_supporting_ids,
        }
        if overlap_ratio >= LINE_DETECTOR_OVERLAP_RATIO_MIN:
            confirmed_lines.append(enriched_line)
            continue
        pixel_only_lines.append(enriched_line)

    return (
        dedupe_lines(confirmed_lines),
        dedupe_lines(pixel_only_lines),
        dedupe_lines(filtered_out_lines),
    )


def bbox_center(bbox: list[list[float]]) -> tuple[float, float] | None:
    if not isinstance(bbox, list) or len(bbox) < 4:
        return None

    try:
        xs = [float(point[0]) for point in bbox]
        ys = [float(point[1]) for point in bbox]
    except (TypeError, ValueError, IndexError):
        return None

    return (sum(xs) / len(xs), sum(ys) / len(ys))


def is_dimension_like_text(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return False
    if re.fullmatch(r"\(?[Øø]?\s*\d+(?:\.\d+)?\)?", cleaned):
        numeric_value = float(re.sub(r"[^\d.]", "", cleaned))
        return numeric_value >= 10.0
    if re.fullmatch(r"\d+\)", cleaned):
        numeric_value = float(re.sub(r"[^\d.]", "", cleaned))
        return numeric_value >= 10.0
    if re.fullmatch(r"\d+(?:\.\d+)?", cleaned):
        numeric_value = float(cleaned)
        return numeric_value >= 10.0
    if re.fullmatch(r"[Øø]\s*\d+(?:\.\d+)?", cleaned):
        numeric_value = float(re.sub(r"[^\d.]", "", cleaned))
        return numeric_value >= 10.0
    if re.fullmatch(r"M\d+(?:\.\d+)?", cleaned, flags=re.IGNORECASE):
        return True
    return False


def build_ocr_candidates(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for detection in detections:
        text = str(detection.get("text", "")).strip()
        bbox = detection.get("bbox", [])
        center = bbox_center(bbox)
        if center is None or not is_dimension_like_text(text):
            continue

        candidates.append(
            {
                "text": text,
                "bbox": bbox,
                "center": center,
                "confidence": float(detection.get("confidence", 0.0)),
            }
        )
    return candidates


def filter_ocr_candidates_to_focus_regions(
    candidates: list[dict[str, Any]],
    focus_regions: list[tuple[int, int, int, int]],
) -> list[dict[str, Any]]:
    if not focus_regions:
        return candidates
    return [candidate for candidate in candidates if any(point_in_rect(candidate["center"], rect) for rect in focus_regions)]


def distance_outside_span(value: float, start: float, end: float, margin: float) -> float:
    lower = min(start, end) - margin
    upper = max(start, end) + margin
    if value < lower:
        return lower - value
    if value > upper:
        return value - upper
    return 0.0


def score_ocr_candidate_for_pair(
    pair: dict[str, Any],
    candidate: dict[str, Any],
) -> float | None:
    start_point = pair["start_point_xy"]
    end_point = pair["end_point_xy"]
    center_x, center_y = candidate["center"]
    midpoint_x, midpoint_y = pair["midpoint"]
    axis = pair["projection_alignment"]["axis"]

    if axis == "h":
        perpendicular_distance = abs(center_y - midpoint_y)
        span_outside_distance = distance_outside_span(center_x, start_point[0], end_point[0], OCR_SPAN_MARGIN)
        midpoint_axis_distance = abs(center_x - midpoint_x)
    else:
        perpendicular_distance = abs(center_x - midpoint_x)
        span_outside_distance = distance_outside_span(center_y, start_point[1], end_point[1], OCR_SPAN_MARGIN)
        midpoint_axis_distance = abs(center_y - midpoint_y)

    if perpendicular_distance > OCR_SEARCH_RADIUS and span_outside_distance > OCR_SPAN_MARGIN:
        return None
    if perpendicular_distance > OCR_PERPENDICULAR_TOLERANCE:
        return None

    confidence = float(candidate.get("confidence", 0.0))
    return (
        perpendicular_distance * OCR_PERPENDICULAR_WEIGHT
        + span_outside_distance * OCR_SPAN_OUTSIDE_WEIGHT
        + midpoint_axis_distance * OCR_MIDPOINT_AXIS_WEIGHT
        - confidence * OCR_CONFIDENCE_BONUS
    )


def match_ocr_to_pair_lines(
    pair_lines: list[dict[str, Any]],
    ocr_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matched_pairs: list[dict[str, Any]] = []
    for pair in pair_lines:
        best_candidate: dict[str, Any] | None = None
        best_score = float("inf")
        for candidate in ocr_candidates:
            score = score_ocr_candidate_for_pair(pair, candidate)
            if score is None or score >= best_score:
                continue
            best_score = score
            best_candidate = candidate

        matched_pairs.append(
            {
                **pair,
                "ocr": best_candidate,
                "ocr_distance": best_score if best_candidate else None,
            }
        )
    return matched_pairs


def unique_ocr_labels(matched_pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for pair in matched_pairs:
        ocr = pair.get("ocr")
        if not ocr:
            continue
        cx, cy = ocr["center"]
        key = (ocr["text"], int(round(cx)), int(round(cy)))
        if key in seen:
            continue
        seen.add(key)
        labels.append(ocr)
    return labels


def draw_text_with_outline(
    canvas: np.ndarray,
    text: str,
    origin: tuple[int, int],
    font_scale: float,
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        canvas,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 0, 0),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        2,
        cv2.LINE_AA,
    )


def render_overlay(
    image: np.ndarray,
    circle_lines: list[dict[str, Any]],
    protrusion_lines: list[dict[str, Any]],
    auxiliary_lines: list[dict[str, Any]],
    projection_endpoints: list[dict[str, float | int]],
    connected_lines: list[dict[str, Any]],
    pixel_only_lines: list[dict[str, Any]],
    matched_pairs: list[dict[str, Any]],
) -> Image.Image:
    base = draw_projection_endpoint_overlay(
        image,
        circle_lines,
        protrusion_lines,
        auxiliary_lines,
        projection_endpoints,
    )
    canvas = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
    height, width = canvas.shape[:2]

    def draw_line(points: np.ndarray, color: tuple[int, int, int], thickness: int) -> None:
        if len(points) >= 2:
            cv2.polylines(canvas, [points], False, color, thickness, cv2.LINE_AA)

    for line in pixel_only_lines:
        waypoints = get_line_waypoints(line)
        points = np.array(
            [[int(round(x)), int(round(y))] for x, y in waypoints],
            dtype=np.int32,
        )
        draw_line(points, PIXEL_ONLY_COLOR, PIXEL_ONLY_THICKNESS)

    for line in connected_lines:
        waypoints = get_line_waypoints(line)
        points = np.array(
            [[int(round(x)), int(round(y))] for x, y in waypoints],
            dtype=np.int32,
        )
        draw_line(points, HYBRID_CONFIRMED_COLOR, HYBRID_CONFIRMED_THICKNESS)

    label_font_scale = max(0.45, min(width, height) / 2500.0)
    for ocr in unique_ocr_labels(matched_pairs):
        bbox = np.array(ocr["bbox"], dtype=np.int32)
        cv2.polylines(canvas, [bbox], True, OCR_BOX_COLOR, 1, cv2.LINE_AA)
        text_x = int(np.min(bbox[:, 0]))
        text_y = int(np.min(bbox[:, 1])) - 8
        text_y = max(24, text_y)
        draw_text_with_outline(
            canvas,
            ocr["text"],
            (text_x, text_y),
            label_font_scale,
            OCR_TEXT_COLOR,
        )

    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def summarize_labels(matched_pairs: list[dict[str, Any]]) -> str:
    labels = [pair["ocr"]["text"] for pair in matched_pairs if pair.get("ocr")]
    if not labels:
        return "-"

    counts: dict[str, int] = {}
    order: list[str] = []
    for label in labels:
        if label not in counts:
            counts[label] = 0
            order.append(label)
        counts[label] += 1

    parts = []
    for label in order:
        count = counts[label]
        if count == 1:
            parts.append(label)
        else:
            parts.append(f"{label} x{count}")
    return ", ".join(parts)


def run() -> None:
    args = parse_args()
    mode = "hybrid validation only" if args.no_ocr else "hybrid validation + OCR"
    print(f"S08 Cardinal v3 - {mode}")
    print("=" * 60)

    targets = [
        (doc_id, gt)
        for doc_id, gt in GT.items()
        if args.doc is None or gt["name"] == args.doc
    ]

    results: list[dict[str, Any]] = []

    for doc_id, gt in targets:
        name = gt["name"]
        image_path = SRC_DIR / f"{doc_id}.png"
        if not image_path.exists():
            print(f"⚠ {name}: {image_path} not found")
            continue

        print(f"\n{name.upper()} - {doc_id}")
        image = cv2.imread(str(image_path))
        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None or gray is None:
            print(f"  ⚠ image load failed: {image_path}")
            continue

        data = collect_projection_data(gray, image_path=image_path)
        circles_full = data["circles_full"]
        if not circles_full:
            print("  ⚠ no primary concentric circles")
            continue

        circle_lines = build_circle_lines(circles_full)
        protrusion_lines = build_protrusion_lines(
            data["peaks_full"],
            data["center_full"],
            data["outer_r"],
        )
        auxiliary_lines = build_auxiliary_lines(
            data["auxiliary_rows"],
            data["center_full"],
            data["section_vertical_cols"],
            data["section_horizontal_rows"],
            data["section_bounds"],
        )
        projection_lines = circle_lines + protrusion_lines + auxiliary_lines
        focus_regions = build_focus_regions(
            image.shape[:2],
            data["main_view_region"],
            data["auxiliary_bounds"],
            data["section_bounds"],
            data["section_vertical_cols"],
        )

        projection_endpoints, lsd_count = build_projection_endpoint_candidates(
            gray,
            projection_lines,
        )
        print(
            f"  projections={len(projection_lines)} | "
            f"lsd_segments={lsd_count} | "
            f"projection_endpoints={len(projection_endpoints)}"
        )

        pixel_candidate_lines, _ = scan_pixel_connections(
            gray,
            projection_endpoints,
            projection_lines,
        )
        pixel_candidate_lines = filter_lines_to_focus_regions(
            pixel_candidate_lines,
            focus_regions,
        )
        line_detector_lines = run_line_detector(image_path)
        connected_lines, pixel_only_lines, filtered_out_lines = validate_pixel_connections_with_line_detector(
            pixel_candidate_lines,
            line_detector_lines,
            image.shape,
            center_full=data["center_full"],
            outer_r=data["outer_r"],
        )
        pair_lines = list(connected_lines)
        print(
            f"  pixel_candidates={len(pixel_candidate_lines)} | "
            f"line_detector_lines={len(line_detector_lines)} | "
            f"hybrid_confirmed={len(connected_lines)} | "
            f"pixel_only={len(pixel_only_lines)} | "
            f"filtered_out={len(filtered_out_lines)}"
        )

        ocr_detections: list[dict[str, Any]] = []
        ocr_candidates: list[dict[str, Any]] = []
        matched_pairs = [
            {**pair, "ocr": None, "ocr_distance": None}
            for pair in pair_lines
        ]
        matched_count = 0
        label_summary = "-"
        if not args.no_ocr:
            ocr_detections = run_ocr(image_path)
            ocr_candidates = build_ocr_candidates(ocr_detections)
            ocr_candidates = filter_ocr_candidates_to_focus_regions(
                ocr_candidates,
                focus_regions,
            )
            matched_pairs = match_ocr_to_pair_lines(pair_lines, ocr_candidates)
            matched_count = sum(1 for pair in matched_pairs if pair.get("ocr"))
            label_summary = summarize_labels(matched_pairs)
            print(
                f"  ocr_detections={len(ocr_detections)} | "
                f"ocr_candidates={len(ocr_candidates)} | "
                f"ocr_matches={matched_count}"
            )
            print(f"  labels={label_summary}")

            # 세션명에서 OD/ID 파싱
            session_odid = parse_session_name_odid(ocr_detections)
            if session_odid:
                print(
                    f"  session_name: {session_odid.get('source_text', '?')} "
                    f"→ OD={session_odid['od']} ID={session_odid['id']}"
                )

        overlay = render_overlay(
            image,
            circle_lines,
            protrusion_lines,
            auxiliary_lines,
            projection_endpoints,
            connected_lines,
            pixel_only_lines,
            matched_pairs,
        )
        output_name = (
            f"{name}_connected_lines.jpg"
            if args.no_ocr
            else f"{name}_line_detector_ocr.jpg"
        )
        save_pil(
            overlay,
            output_name,
            max_w=1600,
            show_size=True,
        )

        results.append(
            {
                "name": name.upper(),
                "connected_lines": len(connected_lines),
                "pair_lines": len(pair_lines),
                "ocr_matches": matched_count,
                "labels": label_summary,
            }
        )

    if not results:
        return

    print("\nMarkdown stats")
    if args.no_ocr:
        print("| 도면 | 연결 선분 수 | 치수선 쌍 수 |")
        print("|------|:---:|:---:|")
    else:
        print("| 도면 | 연결 선분 수 | 치수선 쌍 수 | OCR 매칭 | OCR 라벨 |")
        print("|------|:---:|:---:|:---:|------|")
    for row in results:
        if args.no_ocr:
            print(
                f"| {row['name']} | {row['connected_lines']}개 | "
                f"{row['pair_lines']}개 |"
            )
        else:
            print(
                f"| {row['name']} | {row['connected_lines']}개 | "
                f"{row['pair_lines']}개 | {row['ocr_matches']}개 | {row['labels']} |"
            )


if __name__ == "__main__":
    run()
