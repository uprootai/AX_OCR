#!/usr/bin/env python3
"""S08 Cardinal Projection v3 - Line Detector overlay for sections 2-6/2-7."""

from __future__ import annotations

import argparse
import math
import os
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests
from PIL import Image

from s08_cardinal_v3_endpoint_lines import (
    ENDPOINT_TOLERANCE,
    detect_lsd_segments,
    extract_endpoints,
    filter_endpoints_on_projections,
)
from s08_cardinal_v3_fullpage import (
    GT,
    OUT_DIR,
    SRC_DIR,
    build_auxiliary_lines,
    build_circle_lines,
    build_protrusion_lines,
    collect_projection_data,
    save_pil,
)
from s08_cardinal_v3_projection_endpoints import draw_projection_endpoint_overlay


def resolve_api_url(env_name: str, default_base_url: str, default_path: str) -> str:
    base_url = os.environ.get(env_name, default_base_url).rstrip("/")
    return base_url if base_url.endswith(default_path) else f"{base_url}{default_path}"


LINE_API = resolve_api_url("LINE_DETECTOR_API_URL", "http://localhost:5016", "/api/v1/process")
OCR_API = resolve_api_url("PADDLEOCR_API_URL", "http://localhost:5006", "/api/v1/ocr")

ENDPOINT_TOLERANCE = 20
LINE_MIN_LENGTH = 15
LINE_MAX_LINES = 0  # 0 = 제한 없음
LINE_CONNECTION_RADIUS = 60.0
OCR_SEARCH_RADIUS = 150.0
PROJECTION_AXIS_TOLERANCE = 30.0
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
ENDPOINT_BRIDGE_GAP_MIN = 24.0
ENDPOINT_BRIDGE_GAP_MAX = 90.0
ENDPOINT_BRIDGE_CROSS_AXIS_TOLERANCE = 12.0
ENDPOINT_BRIDGE_STRIP_HALF_WIDTH = 6
ENDPOINT_BRIDGE_DARK_RATIO_MIN = 0.60
ENDPOINT_BRIDGE_LOOKAHEAD = 3
SECTION_BRIDGE_GAP_MAX = 140.0
SECTION_BRIDGE_STRIP_HALF_WIDTH = 8
SECTION_BRIDGE_DARK_RATIO_MIN = 0.45
SECTION_BRIDGE_LOOKAHEAD = 6

CONNECTED_LINE_COLOR = (0, 128, 255)
PAIR_LINE_COLOR = (0, 0, 255)
CONNECTED_LINE_THICKNESS = 5
PAIR_LINE_THICKNESS = 7
SYNTHETIC_BRIDGE_HALO_COLOR = (255, 255, 255)
SYNTHETIC_BRIDGE_HALO_THICKNESS = 13
SYNTHETIC_BRIDGE_THICKNESS = 9
SYNTHETIC_BRIDGE_ENDPOINT_RADIUS = 7
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


def squared_distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]
    return dx * dx + dy * dy


def get_line_endpoints(line: dict[str, Any]) -> tuple[tuple[float, float], tuple[float, float]]:
    start = line.get("start_point", [0.0, 0.0])
    end = line.get("end_point", [0.0, 0.0])
    return (float(start[0]), float(start[1])), (float(end[0]), float(end[1]))


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

    start_point, end_point = get_line_endpoints(line)
    return [start_point, end_point]


def find_line_projection_alignment(
    line: dict[str, Any],
    projection_lines: list[dict[str, Any]],
    start_match: dict[str, Any] | None = None,
    end_match: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    waypoints = get_line_waypoints(line)
    if start_match is not None:
        waypoints[0] = (float(start_match["x"]), float(start_match["y"]))
    if end_match is not None:
        waypoints[-1] = (float(end_match["x"]), float(end_match["y"]))

    best_alignment: dict[str, Any] | None = None
    best_length = -1.0

    for segment_start, segment_end in zip(waypoints, waypoints[1:]):
        if squared_distance(segment_start, segment_end) == 0.0:
            continue

        projection_alignment = find_projection_alignment(
            segment_start,
            segment_end,
            projection_lines,
        )
        if projection_alignment is None:
            continue

        segment_length = math.sqrt(squared_distance(segment_start, segment_end))
        if segment_length <= best_length:
            continue

        best_length = segment_length
        best_alignment = {
            "projection_alignment": projection_alignment,
            "segment_start_point": segment_start,
            "segment_end_point": segment_end,
        }

    return best_alignment


def find_nearest_projection_endpoint(
    point: tuple[float, float],
    endpoints: list[dict[str, float | int]],
    radius: float,
) -> dict[str, Any] | None:
    best_endpoint: dict[str, float | int] | None = None
    best_dist_sq = radius * radius
    for endpoint in endpoints:
        candidate = (float(endpoint["x"]), float(endpoint["y"]))
        dist_sq = squared_distance(point, candidate)
        if dist_sq > best_dist_sq:
            continue
        best_dist_sq = dist_sq
        best_endpoint = endpoint

    if best_endpoint is None:
        return None

    return {
        "endpoint_idx": int(best_endpoint["endpoint_idx"]),
        "segment_idx": int(best_endpoint["segment_idx"]),
        "x": float(best_endpoint["x"]),
        "y": float(best_endpoint["y"]),
        "distance": math.sqrt(best_dist_sq),
    }


def detect_lines_api(image_path: Path) -> list[dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            LINE_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            data={
                "method": "lsd",
                "min_length": str(LINE_MIN_LENGTH),
                "max_lines": str(LINE_MAX_LINES),
                "merge_lines": "true",
                "classify_types": "false",
                "find_intersections": "false",
                "classify_colors": "false",
                "classify_styles": "false",
                "visualize": "false",
            },
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("data", {}).get("lines", [])


def run_ocr(image_path: Path) -> list[dict[str, Any]]:
    with image_path.open("rb") as file_obj:
        response = requests.post(
            OCR_API,
            files={"file": (image_path.name, file_obj, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("detections", [])


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


def find_projection_alignment(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    projection_lines: list[dict[str, Any]],
) -> dict[str, Any] | None:
    horizontal_matches: list[int] = []
    vertical_matches: list[int] = []

    for projection_idx, projection_line in enumerate(projection_lines):
        if projection_line["axis"] == "h":
            py = float(projection_line["py"])
            if (
                abs(start_point[1] - end_point[1]) <= PROJECTION_AXIS_TOLERANCE
                and abs(start_point[1] - py) <= PROJECTION_AXIS_TOLERANCE
                and abs(end_point[1] - py) <= PROJECTION_AXIS_TOLERANCE
            ):
                horizontal_matches.append(projection_idx)
            continue

        px = float(projection_line["px"])
        if (
            abs(start_point[0] - end_point[0]) <= PROJECTION_AXIS_TOLERANCE
            and abs(start_point[0] - px) <= PROJECTION_AXIS_TOLERANCE
            and abs(end_point[0] - px) <= PROJECTION_AXIS_TOLERANCE
        ):
            vertical_matches.append(projection_idx)

    if horizontal_matches:
        return {"axis": "h", "projection_indices": horizontal_matches}
    if vertical_matches:
        return {"axis": "v", "projection_indices": vertical_matches}
    return None


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


def projection_indices_for_endpoint(
    endpoint: dict[str, float | int],
    projection_lines: list[dict[str, Any]],
) -> dict[str, list[int]]:
    point_x = float(endpoint["x"])
    point_y = float(endpoint["y"])
    horizontal_indices: list[int] = []
    vertical_indices: list[int] = []

    for projection_idx, projection_line in enumerate(projection_lines):
        if projection_line["axis"] == "h":
            if abs(point_y - float(projection_line["py"])) <= ENDPOINT_TOLERANCE:
                horizontal_indices.append(projection_idx)
            continue
        if abs(point_x - float(projection_line["px"])) <= ENDPOINT_TOLERANCE:
            vertical_indices.append(projection_idx)

    return {"h": horizontal_indices, "v": vertical_indices}


def projection_gap_already_covered(
    axis: str,
    projection_idx: int,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    pair_lines: list[dict[str, Any]],
) -> bool:
    if axis == "h":
        candidate_start = min(start_point[0], end_point[0])
        candidate_end = max(start_point[0], end_point[0])
        candidate_cross_axis = (start_point[1] + end_point[1]) / 2.0
    else:
        candidate_start = min(start_point[1], end_point[1])
        candidate_end = max(start_point[1], end_point[1])
        candidate_cross_axis = (start_point[0] + end_point[0]) / 2.0

    for line in pair_lines:
        alignment = line["projection_alignment"]
        if alignment["axis"] != axis:
            continue
        if projection_idx not in alignment["projection_indices"]:
            continue

        line_start = line["start_point_xy"]
        line_end = line["end_point_xy"]
        if axis == "h":
            covered_start = min(line_start[0], line_end[0])
            covered_end = max(line_start[0], line_end[0])
            line_cross_axis = (line_start[1] + line_end[1]) / 2.0
        else:
            covered_start = min(line_start[1], line_end[1])
            covered_end = max(line_start[1], line_end[1])
            line_cross_axis = (line_start[0] + line_end[0]) / 2.0

        if abs(line_cross_axis - candidate_cross_axis) > ENDPOINT_BRIDGE_CROSS_AXIS_TOLERANCE:
            continue

        if covered_start <= candidate_start + 4.0 and covered_end >= candidate_end - 4.0:
            return True

    return False


def axis_pixel_support_ratio(
    gray: np.ndarray,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    axis: str,
    strip_half_width: int,
) -> float:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    height, width = binary.shape[:2]

    if axis == "v":
        center_x = int(round((start_point[0] + end_point[0]) / 2.0))
        y1 = max(0, int(round(min(start_point[1], end_point[1]))))
        y2 = min(height - 1, int(round(max(start_point[1], end_point[1]))))
        x1 = max(0, center_x - strip_half_width)
        x2 = min(width, center_x + strip_half_width + 1)
        if y2 <= y1 or x2 <= x1:
            return 0.0

        strip = binary[y1 : y2 + 1, x1:x2]
        support = np.max(strip, axis=1) > 0
        return float(np.mean(support))

    center_y = int(round((start_point[1] + end_point[1]) / 2.0))
    x1 = max(0, int(round(min(start_point[0], end_point[0]))))
    x2 = min(width - 1, int(round(max(start_point[0], end_point[0]))))
    y1 = max(0, center_y - strip_half_width)
    y2 = min(height, center_y + strip_half_width + 1)
    if x2 <= x1 or y2 <= y1:
        return 0.0

    strip = binary[y1:y2, x1 : x2 + 1]
    support = np.max(strip, axis=0) > 0
    return float(np.mean(support))


def in_section_bridge_region(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    section_bounds: tuple[int, int, int, int] | None,
) -> bool:
    if section_bounds is None:
        return False

    midpoint = (
        (start_point[0] + end_point[0]) / 2.0,
        (start_point[1] + end_point[1]) / 2.0,
    )
    expanded = (
        section_bounds[0] - 40,
        section_bounds[1] - 80,
        section_bounds[2] + 40,
        section_bounds[3] + 180,
    )
    return point_in_rect(midpoint, expanded)


def build_projection_gap_bridges(
    gray: np.ndarray,
    projection_endpoints: list[dict[str, float | int]],
    projection_lines: list[dict[str, Any]],
    pair_lines: list[dict[str, Any]],
    section_bounds: tuple[int, int, int, int] | None = None,
) -> list[dict[str, Any]]:
    endpoints_by_projection: dict[tuple[str, int, int], list[dict[str, float | int]]] = {}
    for endpoint in projection_endpoints:
        projection_indices = projection_indices_for_endpoint(endpoint, projection_lines)
        for axis, indices in projection_indices.items():
            lane_coord = float(endpoint["y"]) if axis == "h" else float(endpoint["x"])
            lane_bin = round(lane_coord / ENDPOINT_BRIDGE_CROSS_AXIS_TOLERANCE)
            for projection_idx in indices:
                endpoints_by_projection.setdefault((axis, projection_idx, lane_bin), []).append(endpoint)

    bridges: list[dict[str, Any]] = []
    for (axis, projection_idx, _lane_bin), endpoints in endpoints_by_projection.items():
        if len(endpoints) < 2:
            continue

        sort_key = (
            (lambda item: (float(item["x"]), float(item["y"])))
            if axis == "h"
            else (lambda item: (float(item["y"]), float(item["x"])))
        )
        sorted_endpoints = sorted(endpoints, key=sort_key)

        for start_idx, start_endpoint in enumerate(sorted_endpoints[:-1]):
            start_point = (float(start_endpoint["x"]), float(start_endpoint["y"]))

            max_lookahead = ENDPOINT_BRIDGE_LOOKAHEAD
            if section_bounds is not None and point_in_rect(start_point, section_bounds):
                max_lookahead = SECTION_BRIDGE_LOOKAHEAD

            for end_endpoint in sorted_endpoints[start_idx + 1 : start_idx + 1 + max_lookahead]:
                if int(start_endpoint["endpoint_idx"]) == int(end_endpoint["endpoint_idx"]):
                    continue
                if int(start_endpoint["segment_idx"]) == int(end_endpoint["segment_idx"]):
                    continue

                end_point = (float(end_endpoint["x"]), float(end_endpoint["y"]))

                if axis == "h":
                    gap = abs(end_point[0] - start_point[0])
                    cross_axis_delta = abs(end_point[1] - start_point[1])
                else:
                    gap = abs(end_point[1] - start_point[1])
                    cross_axis_delta = abs(end_point[0] - start_point[0])

                if cross_axis_delta > ENDPOINT_BRIDGE_CROSS_AXIS_TOLERANCE:
                    continue

                in_section = in_section_bridge_region(start_point, end_point, section_bounds)
                gap_max = SECTION_BRIDGE_GAP_MAX if in_section else ENDPOINT_BRIDGE_GAP_MAX
                strip_half_width = (
                    SECTION_BRIDGE_STRIP_HALF_WIDTH if in_section else ENDPOINT_BRIDGE_STRIP_HALF_WIDTH
                )
                dark_ratio_min = (
                    SECTION_BRIDGE_DARK_RATIO_MIN if in_section else ENDPOINT_BRIDGE_DARK_RATIO_MIN
                )

                if gap < ENDPOINT_BRIDGE_GAP_MIN or gap > gap_max:
                    continue
                if projection_gap_already_covered(axis, projection_idx, start_point, end_point, pair_lines):
                    continue

                support_ratio = axis_pixel_support_ratio(
                    gray,
                    start_point,
                    end_point,
                    axis,
                    strip_half_width=strip_half_width,
                )
                if support_ratio < dark_ratio_min:
                    continue

                ordered_start, ordered_end = (
                    (start_point, end_point)
                    if (
                        (axis == "h" and start_point[0] <= end_point[0])
                        or (axis == "v" and start_point[1] <= end_point[1])
                    )
                    else (end_point, start_point)
                )
                ordered_start_match, ordered_end_match = (
                    (start_endpoint, end_endpoint)
                    if ordered_start == start_point
                    else (end_endpoint, start_endpoint)
                )

                bridges.append(
                    {
                        "id": f"bridge-{axis}-{projection_idx}-{int(ordered_start_match['endpoint_idx'])}-{int(ordered_end_match['endpoint_idx'])}",
                        "start_point": ordered_start,
                        "end_point": ordered_end,
                        "waypoints": [list(ordered_start), list(ordered_end)],
                        "length": float(gap),
                        "angle": 0.0 if axis == "h" else 90.0,
                        "synthetic_bridge": True,
                        "bridge_support_ratio": support_ratio,
                        "priority_score": support_ratio * 1000.0 + float(gap),
                        "start_match": {
                            "endpoint_idx": int(ordered_start_match["endpoint_idx"]),
                            "segment_idx": int(ordered_start_match["segment_idx"]),
                            "x": float(ordered_start_match["x"]),
                            "y": float(ordered_start_match["y"]),
                            "distance": 0.0,
                        },
                        "end_match": {
                            "endpoint_idx": int(ordered_end_match["endpoint_idx"]),
                            "segment_idx": int(ordered_end_match["segment_idx"]),
                            "x": float(ordered_end_match["x"]),
                            "y": float(ordered_end_match["y"]),
                            "distance": 0.0,
                        },
                        "projection_alignment": {
                            "axis": axis,
                            "projection_indices": [projection_idx],
                        },
                        "start_point_xy": ordered_start,
                        "end_point_xy": ordered_end,
                        "midpoint": (
                            (ordered_start[0] + ordered_end[0]) / 2.0,
                            (ordered_start[1] + ordered_end[1]) / 2.0,
                        ),
                    }
                )

    return dedupe_lines(bridges)


def filter_connected_lines(
    lines: list[dict[str, Any]],
    projection_endpoints: list[dict[str, float | int]],
    projection_lines: list[dict[str, Any]],
    gray: np.ndarray,
    focus_regions: list[tuple[int, int, int, int]],
    section_bounds: tuple[int, int, int, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    connected_lines: list[dict[str, Any]] = []
    pair_lines: list[dict[str, Any]] = []

    for line in lines:
        start_point, end_point = get_line_endpoints(line)
        start_match = find_nearest_projection_endpoint(
            start_point,
            projection_endpoints,
            radius=LINE_CONNECTION_RADIUS,
        )
        end_match = find_nearest_projection_endpoint(
            end_point,
            projection_endpoints,
            radius=LINE_CONNECTION_RADIUS,
        )

        if start_match is None and end_match is None:
            continue

        projection_alignment_info = find_line_projection_alignment(
            line,
            projection_lines,
            start_match=start_match,
            end_match=end_match,
        )
        if projection_alignment_info is None:
            continue

        aligned_start_point = projection_alignment_info["segment_start_point"]
        aligned_end_point = projection_alignment_info["segment_end_point"]
        annotated = {
            **line,
            "start_match": start_match,
            "end_match": end_match,
            "projection_alignment": projection_alignment_info["projection_alignment"],
            "start_point_xy": aligned_start_point,
            "end_point_xy": aligned_end_point,
            "midpoint": (
                (aligned_start_point[0] + aligned_end_point[0]) / 2.0,
                (aligned_start_point[1] + aligned_end_point[1]) / 2.0,
            ),
        }
        connected_lines.append(annotated)

        if start_match is None or end_match is None:
            continue
        if start_match["endpoint_idx"] == end_match["endpoint_idx"]:
            continue

        pair_lines.append(annotated)

    connected_lines = dedupe_lines(connected_lines)
    pair_lines = dedupe_lines(pair_lines)
    bridge_lines = build_projection_gap_bridges(
        gray,
        projection_endpoints,
        projection_lines,
        pair_lines,
        section_bounds=section_bounds,
    )
    if bridge_lines:
        connected_lines = dedupe_lines(connected_lines + bridge_lines)
        pair_lines = dedupe_lines(pair_lines + bridge_lines)

    connected_lines = filter_lines_to_focus_regions(connected_lines, focus_regions)
    pair_lines = filter_lines_to_focus_regions(pair_lines, focus_regions)

    return connected_lines, pair_lines


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

    def draw_line(points: np.ndarray, color: tuple[int, int, int], thickness: int) -> None:
        if len(points) >= 2:
            cv2.polylines(canvas, [points], False, color, thickness, cv2.LINE_AA)

    regular_lines: list[dict[str, Any]] = []
    synthetic_bridge_lines: list[dict[str, Any]] = []
    for line in connected_lines:
        if line.get("synthetic_bridge"):
            synthetic_bridge_lines.append(line)
            continue
        regular_lines.append(line)

    # Draw standard line-detector segments after projection lines/endpoints.
    for line in regular_lines:
        is_pair = line.get("start_match") is not None and line.get("end_match") is not None
        color = PAIR_LINE_COLOR if is_pair else CONNECTED_LINE_COLOR
        thickness = PAIR_LINE_THICKNESS if is_pair else CONNECTED_LINE_THICKNESS
        waypoints = get_line_waypoints(line)
        points = np.array(
            [[int(round(x)), int(round(y))] for x, y in waypoints],
            dtype=np.int32,
        )
        draw_line(points, color, thickness)

    # Synthetic bridges are short and easily buried in hatching after resize/JPEG.
    # Draw them last with a white halo so the recovered segment remains visible.
    for line in synthetic_bridge_lines:
        waypoints = get_line_waypoints(line)
        points = np.array(
            [[int(round(x)), int(round(y))] for x, y in waypoints],
            dtype=np.int32,
        )
        if len(points) < 2:
            continue

        draw_line(points, SYNTHETIC_BRIDGE_HALO_COLOR, SYNTHETIC_BRIDGE_HALO_THICKNESS)
        draw_line(points, PAIR_LINE_COLOR, SYNTHETIC_BRIDGE_THICKNESS)
        for point in points[[0, -1]]:
            cv2.circle(
                canvas,
                tuple(point),
                SYNTHETIC_BRIDGE_ENDPOINT_RADIUS,
                SYNTHETIC_BRIDGE_HALO_COLOR,
                -1,
                cv2.LINE_AA,
            )
            cv2.circle(
                canvas,
                tuple(point),
                max(3, SYNTHETIC_BRIDGE_ENDPOINT_RADIUS - 2),
                PAIR_LINE_COLOR,
                -1,
                cv2.LINE_AA,
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
    mode = "connected lines only" if args.no_ocr else "line detector + OCR"
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

        line_detector_lines = detect_lines_api(image_path)
        connected_lines, pair_lines = filter_connected_lines(
            line_detector_lines,
            projection_endpoints,
            projection_lines,
            gray,
            focus_regions,
            section_bounds=data["section_bounds"],
        )
        print(
            f"  line_detector={len(line_detector_lines)} | "
            f"connected_lines={len(connected_lines)} | "
            f"pair_lines={len(pair_lines)}"
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
            matched_pairs,
        )
        output_name = (
            f"{name}_connected_lines.jpg"
            if args.no_ocr
            else f"{name}_line_detector_ocr.jpg"
        )
        save_pil(overlay, output_name, max_w=1600)

        results.append(
            {
                "name": name.upper(),
                "line_detector": len(line_detector_lines),
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
        print("| 도면 | Line Detector 선분 수 | 연결 선분 수 | 치수선 쌍 수 |")
        print("|------|:---:|:---:|:---:|")
    else:
        print("| 도면 | Line Detector 선분 수 | 연결 선분 수 | 치수선 쌍 수 | OCR 매칭 | OCR 라벨 |")
        print("|------|:---:|:---:|:---:|:---:|------|")
    for row in results:
        if args.no_ocr:
            print(
                f"| {row['name']} | {row['line_detector']}개 | "
                f"{row['connected_lines']}개 | {row['pair_lines']}개 |"
            )
        else:
            print(
                f"| {row['name']} | {row['line_detector']}개 | {row['connected_lines']}개 | "
                f"{row['pair_lines']}개 | {row['ocr_matches']}개 | {row['labels']} |"
            )


if __name__ == "__main__":
    run()
